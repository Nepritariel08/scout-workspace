"""Conversation-bound review and recovery; no caller-selected queue records."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.db.models import Event, Turn
from app.routers.threads import _thread_or_404, get_runtime
from app.services import thread_store as store
from app.services.local_access_policy import require_local_access
from app.services.scout_queue import QueueBinding, QueueError, connect, snapshot
from app.services.thread_runtime import ThreadRuntime

router = APIRouter(prefix="/threads", tags=["Scout queue"], dependencies=[Depends(require_local_access)])


class ScoutAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["refresh", "recover", "accept", "cancel"]
    revision: int | None = Field(default=None, ge=0)


def error(code, message, status=409):
    return HTTPException(status, detail={"error_code": code, "message": message})


@router.post("/{thread_id}/scout/{turn_id}")
async def scout_action(thread_id: int, turn_id: int, payload: ScoutAction,
                       rt: ThreadRuntime = Depends(get_runtime)):
    thread = await _thread_or_404(rt, thread_id)
    if thread.provider != "scout_queue":
        raise error("scout_wrong_engine", "This conversation does not use the Scout queue.")
    async with rt.session() as db:
        turn = await db.get(Turn, turn_id)
        events = list((await db.execute(select(Event).where(
            Event.thread_id == thread_id, Event.turn_id == turn_id,
            Event.type.in_(("scout.requested", "scout.work")),
        ).order_by(Event.seq))).scalars())
    if turn is None or turn.thread_id != thread_id:
        raise HTTPException(404, "Task not found")
    requested = next((e.data for e in events if e.type == "scout.requested"), None)
    receipts = [e.data for e in events if e.type == "scout.work"]
    if requested is None:
        raise HTTPException(404, "Scout submission not found")
    try:
        binding = QueueBinding.configured()
        binding.require_owner(rt.owner_id)
        if requested.get("binding") != binding.fingerprint:
            raise QueueError("scout_binding_changed", "The requester binding changed. Restore the original binding before recovery.")
        if payload.action == "recover" and turn.status == "running":
            raise error("scout_turn_running", "This task is still being submitted by its active turn.")
        async with connect(binding) as queue:
            if receipts:
                item = await queue.get(receipts[-1]["id"], requested["request_key"])
            elif payload.action == "recover":
                # Exact stored payload + original request key. Odoo resolves a lost
                # reply to the existing item; it does not authorize a second execution.
                item = await queue.submit({k: requested[k] for k in ("title", "instructions", "request_key")})
            else:
                raise error("scout_submission_unknown", "Recover the original submission before reviewing its result.")
            if payload.action in {"accept", "cancel"}:
                target = "completed" if payload.action == "accept" else "cancelled"
                if item["state"] != target:
                    if payload.revision is None or payload.revision != item["revision"]:
                        raise error("scout_stale_revision", "The task changed. Refresh and review its current receipt first.")
                    if payload.action == "accept" and (item["state"] != "review_required" or not item.get("result")):
                        raise error("scout_no_draft", "Only a returned draft can be accepted.")
                    item = await queue.change(payload.action, item["id"], item["revision"], requested["request_key"])
                    item = await queue.get(item["id"], requested["request_key"])
                    if item["state"] != target:
                        raise error("scout_action_unconfirmed", "The action was not confirmed; refresh the receipt.")
            receipt = snapshot(item)
        if not receipts or receipts[-1] != receipt:
            async with rt.session() as db:
                await store.append_event(db, thread_id, "scout.work", receipt, turn_id=turn_id)
            rt.hub.notify(thread_id)
        return receipt
    except QueueError as exc:
        raise error(exc.code, str(exc), 503) from None
