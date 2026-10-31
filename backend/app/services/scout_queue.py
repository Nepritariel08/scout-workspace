"""Requester-only MCP bridge to the existing Odoo/DSH queue.

The application stores conversation receipts, not another execution queue. A
persisted submission contains the exact idempotent payload needed after a lost
reply. Only the separately installed worker may claim or execute that work.
"""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from mcp import Client, StdioServerParameters

from app.core.config import settings
from app.services.provider_adapter import Capabilities, EngineProbe, ProviderStatus, TurnOutcome

TOOLS = {"scout_queue_status", "scout_list_work", "scout_get_work", "scout_submit_work",
         "scout_accept_draft", "scout_cancel_work"}
ENV_KEYS = {"SCOUT_ODOO_URL", "SCOUT_ODOO_DB", "SCOUT_ODOO_UID",
            "SCOUT_ODOO_COMPANY_IDS", "SCOUT_ODOO_KEY_FILE"}
STATES = {"queued", "running", "review_required", "completed", "cancelled", "failed"}
TERMINAL = {"review_required", "completed", "cancelled", "failed"}
RPC_TIMEOUT = 15


class QueueError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class QueueBinding:
    command: tuple[str, ...]
    cwd: str
    environment: dict[str, str] = field(repr=False)
    client_id: str
    owner_id: str
    poll_seconds: float = 2
    wait_seconds: float = 300

    def __post_init__(self):
        env = self.environment
        try:
            origin = urlsplit(env["SCOUT_ODOO_URL"])
            uid = int(env["SCOUT_ODOO_UID"])
            companies = [int(x) for x in env["SCOUT_ODOO_COMPANY_IDS"].split(",")]
            valid = (
                len(self.command) == 3 and Path(self.command[0]).is_absolute()
                and self.command[1:] == ("-m", "scout_queue.mcp_server")
                and Path(self.cwd).is_absolute() and Path(self.cwd).is_dir()
                and set(env) == ENV_KEYS and all(isinstance(v, str) for v in env.values())
                and origin.scheme in {"http", "https"} and origin.hostname
                and not origin.username and not origin.password and not origin.query and not origin.fragment
                and origin.path in {"", "/"}
                and (origin.scheme == "https" or origin.hostname in {"127.0.0.1", "localhost", "::1"})
                and re.fullmatch(r"[A-Za-z0-9_-]{1,100}", env["SCOUT_ODOO_DB"])
                and uid > 0 and companies and min(companies) > 0 and len(set(companies)) == len(companies)
                and Path(env["SCOUT_ODOO_KEY_FILE"]).is_absolute()
                and re.fullmatch(r"[A-Za-z0-9_-]{1,48}", self.client_id)
                and isinstance(self.owner_id, str) and 1 <= len(self.owner_id) <= 200
                and 0.1 <= self.poll_seconds <= 30 and 1 <= self.wait_seconds <= 3600
            )
        except (KeyError, TypeError, ValueError, OSError):
            valid = False
        if not valid:
            raise QueueError("scout_binding_invalid", "The server's Scout queue binding is invalid.")

    @classmethod
    def configured(cls):
        try:
            path = Path(settings.SCOUT_QUEUE_CONFIG_FILE)
            if not settings.SCOUT_QUEUE_CONFIG_FILE or not path.is_absolute() or path.is_symlink():
                raise ValueError()
            if os.name == "posix" and path.stat().st_mode & 0o077:
                raise ValueError()
            if path.stat().st_size > 16384:
                raise ValueError()
            raw = json.loads(path.read_text(encoding="utf-8"))
            if set(raw) - {"command", "cwd", "environment", "client_id", "owner_id", "poll_seconds", "wait_seconds"}:
                raise ValueError()
            return cls(tuple(raw["command"]), raw["cwd"], raw["environment"], raw["client_id"], raw["owner_id"],
                       float(raw.get("poll_seconds", 2)), float(raw.get("wait_seconds", 300)))
        except (OSError, ValueError, TypeError, KeyError):
            raise QueueError("scout_not_configured", "Configure the server's protected Scout queue binding first.") from None

    @property
    def identity(self):
        return {"database": self.environment["SCOUT_ODOO_DB"],
                "uid": int(self.environment["SCOUT_ODOO_UID"]),
                "company_ids": sorted(int(x) for x in self.environment["SCOUT_ODOO_COMPANY_IDS"].split(","))}

    @property
    def fingerprint(self):
        return digest({**self.identity, "origin": self.environment["SCOUT_ODOO_URL"].rstrip("/"),
                       "client_id": self.client_id, "owner_id": self.owner_id})

    def require_owner(self, owner_id):
        if owner_id != self.owner_id:
            raise QueueError("scout_owner_mismatch", "This application account has no approved Scout queue binding.")


class QueueSession:
    def __init__(self, binding: QueueBinding, rpc):
        self.binding, self.rpc = binding, rpc

    async def _tool(self, name, arguments=None):
        if name not in TOOLS:
            raise QueueError("scout_tool_forbidden", "The Scout engine exposes requester operations only.")
        try:
            async with asyncio.timeout(RPC_TIMEOUT):
                result = await self.rpc.call_tool(name, arguments or {})
            if result.is_error:
                raise ValueError()
            value = result.structured_content
            if value is None:
                text = "".join(getattr(c, "text", "") for c in result.content)
                if len(text) > 100000:
                    raise ValueError()
                value = json.loads(text)
            if not isinstance(value, dict) or len(json.dumps(value)) > 100000:
                raise ValueError()
            return value
        except asyncio.CancelledError:
            raise
        except Exception:
            # MCP/server exceptions can contain remote error text. Never forward it.
            raise QueueError("scout_queue_unavailable", "The queue operation was not confirmed. Refresh its receipt before retrying.") from None

    async def verify(self):
        value = await self._tool("scout_queue_status")
        expected = self.binding.identity
        companies = value.get("company_ids")
        if (value.get("database") != expected["database"] or type(value.get("uid")) is not int
                or value["uid"] != expected["uid"] or not isinstance(companies, list)
                or any(type(c) is not int for c in companies) or sorted(companies) != expected["company_ids"]
                or value.get("worker") is not False or value.get("business_actions_enabled") is not False
                or value.get("task_kinds") != ["draft_analysis"]):
            raise QueueError("scout_identity_changed", "The queue's requester identity, company or capability binding changed.")
        return value

    def item(self, value, *, request_key=None, work_item_id=None):
        expected = self.binding.identity
        valid = (type(value.get("id")) is int and value["id"] > 0
                 and type(value.get("revision")) is int and value["revision"] >= 0
                 and value.get("state") in STATES and value.get("task_kind") == "draft_analysis"
                 and type(value.get("requested_by")) is int and type(value.get("company_id")) is int
                 and value.get("requested_by") == expected["uid"]
                 and value.get("company_id") in expected["company_ids"]
                 and isinstance(value.get("request_key"), str)
                 and (value.get("result") is None or isinstance(value["result"], str) and len(value["result"]) <= 20000)
                 and (request_key is None or value["request_key"] == request_key)
                 and (work_item_id is None or value["id"] == work_item_id))
        if not valid:
            raise QueueError("scout_receipt_mismatch", "The queue receipt does not match this request and requester.")
        return value

    async def submit(self, payload):
        await self.verify()
        return self.item(await self._tool("scout_submit_work", payload), request_key=payload["request_key"])

    async def get(self, item_id, request_key):
        await self.verify()
        return self.item(await self._tool("scout_get_work", {"work_item_id": item_id}),
                         work_item_id=item_id, request_key=request_key)

    async def change(self, action, item_id, revision, request_key):
        await self.verify()
        if action not in {"accept", "cancel"}:
            raise QueueError("scout_tool_forbidden", "Unknown Scout requester action.")
        name = "scout_accept_draft" if action == "accept" else "scout_cancel_work"
        return self.item(await self._tool(name, {"work_item_id": item_id, "revision": revision}),
                         work_item_id=item_id, request_key=request_key)


@asynccontextmanager
async def connect(binding: QueueBinding, *, client_factory=Client):
    environment = {k: v for k, v in os.environ.items()
                   if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL", "SSL_CERT_FILE"}}
    environment.update(binding.environment)
    params = StdioServerParameters(command=binding.command[0], args=list(binding.command[1:]),
                                   cwd=binding.cwd, env=environment)
    stack = AsyncExitStack()
    try:
        try:
            rpc = await stack.enter_async_context(client_factory(params))
            async with asyncio.timeout(RPC_TIMEOUT):
                tools = await rpc.list_tools()
            if {t.name for t in tools.tools} != TOOLS or len(tools.tools) != len(TOOLS):
                raise QueueError("scout_toolset_changed", "The connector no longer exposes the six approved requester tools.")
            queue = QueueSession(binding, rpc)
            await queue.verify()
        except (QueueError, asyncio.CancelledError):
            raise
        except Exception:
            raise QueueError("scout_queue_unavailable", "The configured Scout connector is unavailable.") from None
        # Consumer errors (including HTTP conflicts) must not be passed into the
        # MCP task group, which would wrap them as transport exception groups.
        yield queue
    finally:
        await stack.aclose()


def snapshot(item):
    """Only a receipt is mirrored in conversation events; Odoo owns its state."""
    return {k: item.get(k) for k in ("id", "state", "revision", "request_key", "result", "error_code", "dsh_session_id")}


class ScoutQueueAdapter:
    key = "scout_queue"
    label = "Scout · DSH queue"
    kind = "api"
    capabilities = Capabilities(resume=True)
    custom_models = False
    models = []
    needs_config = False

    def __init__(self, binding=None, connector=connect):
        self.binding, self.connector = binding, connector

    def configuration(self):
        return self.binding or QueueBinding.configured()

    def new_session_id(self):
        return None

    async def status(self):
        try:
            async with self.connector(self.configuration()):
                return ProviderStatus(ready=True, installed=True, signed_in=True)
        except QueueError as exc:
            return ProviderStatus(ready=False, installed=False, error=str(exc))

    async def probe(self):
        status = await self.status()
        return EngineProbe(installed=bool(status.installed), ready=status.ready, reason=status.error)

    async def run_turn(self, ctx, sink, gate):
        stopped = asyncio.Event()
        loop = asyncio.get_running_loop()
        ctx.on_abort(lambda: loop.call_soon_threadsafe(stopped.set))
        item = None
        payload = None
        try:
            binding = self.configuration()
            binding.require_owner(ctx.owner_id)
            history = await ctx.history()
            parts = [ctx.instructions or ""]
            # history_items uses text, and includes the current user message.
            # The enriched current prompt replaces that last raw message.
            if history and history[-1].get("role") == "user":
                history = history[:-1]
            for message in history:
                content = message.get("text", "")
                if isinstance(content, str):
                    parts.append(f"{message.get('role', 'message')}: {content}")
            parts.append(f"Requester task: {ctx.prompt}")
            instructions = "\n\n".join(p for p in parts if p).strip()
            if not instructions or len(instructions) > 8000:
                raise QueueError("scout_context_limit", "The task and conversation context must fit the queue's 8,000-character limit.")
            payload = {"title": ctx.prompt.strip()[:100] or "Scout draft",
                       "instructions": instructions,
                       "request_key": f"scout.{binding.client_id}.{ctx.thread_id}.{ctx.turn_id}"}
            async with self.connector(binding) as queue:
                if ctx.aborted:
                    return TurnOutcome("cancelled")
                if not await sink.emit("scout.requested", {**payload, "binding": binding.fingerprint}):
                    return TurnOutcome("failed", error_code="lost")
                item = await queue.submit(payload)
                if not await sink.emit("scout.work", snapshot(item)):
                    return TurnOutcome("failed", error_code="lost")
                deadline = loop.time() + binding.wait_seconds
                last_notice = loop.time()
                while item["state"] not in TERMINAL:
                    if stopped.is_set():
                        break
                    if loop.time() >= deadline:
                        raise QueueError("scout_wait_timeout", "The queue is still working. Refresh this task's receipt; do not submit it again.")
                    try:
                        await asyncio.wait_for(stopped.wait(), binding.poll_seconds)
                    except TimeoutError:
                        pass
                    if stopped.is_set():
                        break
                    current = await queue.get(item["id"], payload["request_key"])
                    if current["revision"] != item["revision"] or loop.time() - last_notice >= 15:
                        if not await sink.emit("scout.work", snapshot(current)):
                            return TurnOutcome("failed", error_code="lost")
                        last_notice = loop.time()
                    item = current
                if stopped.is_set():
                    if getattr(ctx, "stop_requested", False):
                        item = await queue.get(item["id"], payload["request_key"])
                        if item["state"] != "cancelled" and item["state"] != "completed":
                            item = await queue.change("cancel", item["id"], item["revision"], payload["request_key"])
                        await sink.emit("scout.work", snapshot(item))
                        return TurnOutcome("cancelled")
                    # Application shutdown/lease loss must not cancel an always-on worker.
                    return TurnOutcome("failed", error_code="scout_detached",
                                       error="The conversation detached. Recover the existing queue receipt after reconnecting.")
                if item["state"] in {"review_required", "completed"} and item.get("result"):
                    await sink.emit("assistant.message", {"text": item["result"]})
                    return TurnOutcome("succeeded", result=item["result"])
                if item["state"] == "cancelled":
                    return TurnOutcome("cancelled")
                raise QueueError("scout_review_required", "The queue needs review. Inspect its receipt before creating another request.")
        except QueueError as exc:
            return TurnOutcome("failed", error=str(exc), error_code=exc.code)
