"""Real MCP sessions and committed conversation receipts; no live provider."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import sys

import httpx
from fastapi import FastAPI
from mcp import Client
from mcp.server import MCPServer
import pytest

from app.core.config import settings
from app.routers import scout_queue as route
from app.routers.threads import get_runtime
from app.services.scout_queue import QueueBinding, QueueError, ScoutQueueAdapter, connect
from app.services.provider_adapter import TurnContext
from app.services.thread_hub import ThreadHub
from app.services.thread_runtime import ThreadRuntime
from tests.services.thread_harness import cleanup, events_of, finished, owner, sessions  # noqa: F401


class QueueFixture:
    def __init__(self):
        self.items = {}
        self.submit_calls = 0
        self.cancel_calls = 0
        self.accept_calls = 0
        self.worker = False
        self.lose_reply = False
        self.auto_finish = True
        self.submitted = asyncio.Event()

    def status(self):
        return {"database": "qa", "uid": 7, "company_ids": [1], "worker": self.worker,
                "task_kinds": ["draft_analysis"], "business_actions_enabled": False}

    def submit(self, title, instructions, request_key):
        self.submit_calls += 1
        existing = next((x for x in self.items.values() if x["request_key"] == request_key), None)
        if existing is None:
            existing = {"id": len(self.items) + 1, "revision": 1, "state": "queued", "task_kind": "draft_analysis",
                        "requested_by": 7, "company_id": 1, "request_key": request_key, "result": None,
                        "instructions": instructions, "title": title, "error_code": None, "dsh_session_id": None}
            self.items[existing["id"]] = existing
        assert existing["instructions"] == instructions and existing["title"] == title
        self.submitted.set()
        if self.lose_reply:
            self.lose_reply = False
            raise RuntimeError("fixture lost response")
        return dict(existing)

    def get(self, item_id):
        item = self.items[item_id]
        if self.auto_finish and item["state"] == "queued":
            item.update(state="review_required", revision=3, result="Returned draft", dsh_session_id="fixture-dsh")
        return dict(item)

    def change(self, action, item_id, revision):
        item = self.items[item_id]
        assert item["revision"] == revision
        if action == "accept":
            assert item["state"] == "review_required"
            self.accept_calls += 1
            item["state"] = "completed"
        else:
            self.cancel_calls += 1
            item["state"] = "cancelled"
        item["revision"] += 1
        return dict(item)

    def server(self):
        server = MCPServer("Queue fixture")
        @server.tool()
        def scout_queue_status() -> dict: return self.status()
        @server.tool()
        def scout_submit_work(title: str, instructions: str, request_key: str) -> dict:
            return self.submit(title, instructions, request_key)
        @server.tool()
        def scout_get_work(work_item_id: int) -> dict: return self.get(work_item_id)
        @server.tool()
        def scout_list_work() -> dict: return {"items": []}
        @server.tool()
        def scout_accept_draft(work_item_id: int, revision: int) -> dict: return self.change("accept", work_item_id, revision)
        @server.tool()
        def scout_cancel_work(work_item_id: int, revision: int) -> dict: return self.change("cancel", work_item_id, revision)
        return server


@pytest.fixture
def queue_setup(tmp_path, monkeypatch, owner):
    fixture = QueueFixture()
    binding = QueueBinding((sys.executable, "-m", "scout_queue.mcp_server"), str(tmp_path), {
        "SCOUT_ODOO_URL": "http://127.0.0.1:18089", "SCOUT_ODOO_DB": "qa", "SCOUT_ODOO_UID": "7",
        "SCOUT_ODOO_COMPANY_IDS": "1", "SCOUT_ODOO_KEY_FILE": str(tmp_path / "requester.key"),
    }, "qa-owner", owner, poll_seconds=0.1, wait_seconds=5)
    server = fixture.server()
    @asynccontextmanager
    async def connector(value):
        async with connect(value, client_factory=lambda params: Client(server)) as queue:
            yield queue
    monkeypatch.setattr(QueueBinding, "configured", classmethod(lambda cls: binding))
    monkeypatch.setattr(route, "connect", connector)
    return fixture, binding, connector


@pytest.fixture
async def scout_rt(queue_setup, sessions, owner, monkeypatch):
    fixture, binding, connector = queue_setup
    monkeypatch.setattr(settings, "LOCAL_EXECUTION_ENABLED", True)
    monkeypatch.setattr(settings, "THREAD_HEARTBEAT_SECONDS", 0.2)
    runtime = ThreadRuntime(hub=ThreadHub(), adapters={"scout_queue": ScoutQueueAdapter(binding, connector)},
                            _session_factory=sessions, owner_id=owner, status_ttl=0)
    yield runtime
    await runtime.shutdown()


def app_for(runtime):
    app = FastAPI()
    app.include_router(route.router, prefix="/api/v1")
    app.dependency_overrides[get_runtime] = lambda: runtime
    return app


async def test_round_trip_and_acceptance_stay_in_the_originating_conversation(scout_rt, sessions, queue_setup):
    fixture, _, _ = queue_setup
    thread = await scout_rt.create_thread(provider="scout_queue")
    turn = await scout_rt.send_turn(thread.id, "Draft a short summary")
    await finished(sessions, thread.id)
    events = await events_of(sessions, thread.id)
    assert [e.data["text"] for e in events if e.type == "assistant.message"] == ["Returned draft"]
    assert fixture.submit_calls == 1
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app_for(scout_rt)), base_url="http://localhost") as api:
        response = await api.post(f"/api/v1/threads/{thread.id}/scout/{turn.id}", json={"action": "accept", "revision": 3})
        assert response.status_code == 200, response.text
        assert response.json()["state"] == "completed"
        # A lost acceptance response is reconciled by readback, without another mutation.
        response = await api.post(f"/api/v1/threads/{thread.id}/scout/{turn.id}", json={"action": "accept", "revision": 3})
        assert response.status_code == 200
    assert fixture.accept_calls == 1 and fixture.submit_calls == 1


async def test_lost_submit_response_recovers_the_exact_stored_payload(scout_rt, sessions, queue_setup):
    fixture, _, _ = queue_setup
    fixture.lose_reply = True
    thread = await scout_rt.create_thread(provider="scout_queue")
    turn = await scout_rt.send_turn(thread.id, "Original task")
    await finished(sessions, thread.id)
    assert len(fixture.items) == 1
    # A newly constructed runtime reads the original intent from SQLite after
    # the first runtime has shut down; no in-memory state is carried over.
    await scout_rt.shutdown()
    restarted = ThreadRuntime(hub=ThreadHub(), adapters=scout_rt.adapters,
                              _session_factory=sessions, owner_id=scout_rt.owner_id)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app_for(restarted)), base_url="http://localhost") as api:
        result = await api.post(f"/api/v1/threads/{thread.id}/scout/{turn.id}", json={"action": "recover"})
        assert result.status_code == 200, result.text
        assert result.json()["id"] == 1
        result = await api.post(f"/api/v1/threads/{thread.id}/scout/{turn.id}", json={"action": "refresh"})
        assert result.json()["result"] == "Returned draft"
    assert len(fixture.items) == 1 and fixture.submit_calls == 2
    await restarted.shutdown()


async def test_stale_acceptance_and_other_conversations_are_refused(scout_rt, sessions, queue_setup):
    fixture, _, _ = queue_setup
    thread = await scout_rt.create_thread(provider="scout_queue")
    other = await scout_rt.create_thread(provider="scout_queue")
    turn = await scout_rt.send_turn(thread.id, "Draft")
    await finished(sessions, thread.id)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app_for(scout_rt)), base_url="http://localhost") as api:
        response = await api.post(f"/api/v1/threads/{thread.id}/scout/{turn.id}", json={"action": "accept", "revision": 1})
        assert response.status_code == 409
        response = await api.post(f"/api/v1/threads/{other.id}/scout/{turn.id}", json={"action": "accept", "revision": 3})
        assert response.status_code == 404
    assert fixture.accept_calls == 0


async def test_worker_identity_is_never_accepted_as_a_requester(queue_setup):
    fixture, binding, connector = queue_setup
    fixture.worker = True
    with pytest.raises(QueueError, match="requester identity"):
        async with connector(binding):
            pass
    assert fixture.submit_calls == 0


async def test_different_application_owner_cannot_borrow_the_odoo_binding(queue_setup):
    fixture, binding, connector = queue_setup
    async def history(): return []
    ctx = TurnContext(1, 1, "Draft", None, None, None, None, False, history, owner_id="another-owner")
    outcome = await ScoutQueueAdapter(binding, connector).run_turn(ctx, None, None)
    assert outcome.error_code == "scout_owner_mismatch" and fixture.submit_calls == 0


async def test_history_and_current_context_are_preserved_once(queue_setup):
    fixture, binding, connector = queue_setup
    async def history():
        return [{"role": "user", "text": "First question"},
                {"role": "assistant", "text": "Earlier answer"},
                {"role": "user", "text": "Current question"}]
    ctx = TurnContext(1, 1, "Current question with attachment", None, None, None, None, False, history,
                      owner_id=binding.owner_id, instructions="Draft only")
    class Sink:
        async def emit(self, type, data): return True
    outcome = await ScoutQueueAdapter(binding, connector).run_turn(ctx, Sink(), None)
    assert outcome.status == "succeeded"
    instructions = fixture.items[1]["instructions"]
    assert instructions == "Draft only\n\nuser: First question\n\nassistant: Earlier answer\n\nRequester task: Current question with attachment"


@pytest.mark.parametrize("user_stop", [False, True])
async def test_stop_cancels_but_backend_detachment_preserves_remote_work(queue_setup, user_stop):
    fixture, binding, connector = queue_setup
    fixture.auto_finish = False
    async def history(): return []
    ctx = TurnContext(1, 1, "Draft", None, None, None, None, False, history)
    ctx.owner_id = binding.owner_id
    class Sink:
        async def emit(self, type, data): return True
    task = asyncio.create_task(ScoutQueueAdapter(binding, connector).run_turn(ctx, Sink(), None))
    await asyncio.wait_for(fixture.submitted.wait(), 3)
    ctx.stop_requested = user_stop
    ctx.abort()
    outcome = await asyncio.wait_for(task, 3)
    assert fixture.cancel_calls == int(user_stop)
    assert fixture.items[1]["state"] == ("cancelled" if user_stop else "queued")
    assert outcome.status == ("cancelled" if user_stop else "failed")
