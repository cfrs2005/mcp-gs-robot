"""Agent chat sessions, SSE streaming and user confirmations."""

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from contextlib import suppress

import anyio
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .. import deps

router = APIRouter(prefix="/agent/sessions")
logger = logging.getLogger(__name__)


class MessageInput(BaseModel):
    content: str


class SessionInput(BaseModel):
    title: str | None = None


class ConfirmationInput(BaseModel):
    confirm_id: str
    approve: bool


class PendingConfirms:
    """Confirmation futures are scoped to both session and confirm ID."""

    def __init__(self) -> None:
        self.pending: dict[str, tuple[str, asyncio.Future[bool]]] = {}
        self.waiting: set[str] = set()
        self.busy: set[str] = set()

    def prepare(self, session_id: str, confirm_id: str) -> None:
        if confirm_id in self.pending:
            raise ValueError("Confirmation already pending")
        self.pending[confirm_id] = (session_id, asyncio.get_running_loop().create_future())
        self.waiting.add(session_id)

    async def ask(
        self, session_id: str, confirm_id: str, name: str, input: dict, summary: str,
    ) -> bool:
        entry = self.pending.get(confirm_id)
        if entry is None:
            self.prepare(session_id, confirm_id)
            entry = self.pending[confirm_id]
        if entry[0] != session_id:
            raise ValueError("Confirmation belongs to another session")
        _, future = entry
        try:
            return await asyncio.wait_for(future, timeout=120)
        except TimeoutError:
            return False
        finally:
            self.pending.pop(confirm_id, None)
            if not any(owner == session_id for owner, _ in self.pending.values()):
                self.waiting.discard(session_id)

    def resolve(self, session_id: str, confirm_id: str, approve: bool) -> None:
        entry = self.pending.get(confirm_id)
        if entry is None or entry[0] != session_id or entry[1].done():
            raise HTTPException(status_code=404, detail="Confirmation not found")
        entry[1].set_result(approve)

    def clear(self, session_id: str) -> None:
        for confirm_id, (owner, future) in list(self.pending.items()):
            if owner == session_id:
                if not future.done():
                    future.cancel()
                self.pending.pop(confirm_id)
        self.waiting.discard(session_id)
        self.busy.discard(session_id)


@router.post("")
async def create_session(sessions: deps.SessionsDep, body: SessionInput | None = None) -> dict:
    session = await sessions.create(body.title if body else None)
    return {"session_id": session.session_id}


@router.get("")
async def list_sessions(
    sessions: deps.SessionsDep, page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100), include_empty: bool = False,
) -> dict:
    items, total = await sessions.page(page, page_size, include_empty)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{session_id}")
async def get_session(session_id: str, sessions: deps.SessionsDep) -> dict:
    session = await sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "title": session.title,
        "messages": session.messages,
        "errors": session.errors,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "message_count": len(session.messages),
    }


@router.delete("/{session_id}")
async def delete_session(
    session_id: str, sessions: deps.SessionsDep,
    confirms: deps.ConfirmsDep,
) -> dict:
    if await sessions.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_id in confirms.busy:
        raise HTTPException(status_code=409, detail="Session is busy")
    await sessions.delete(session_id)
    return {"ok": True}


@router.post("/{session_id}/messages")
async def message(
    session_id: str, body: MessageInput, request: Request, sessions: deps.SessionsDep,
    agent: deps.AgentDep, confirms: deps.ConfirmsDep,
) -> StreamingResponse:
    session = await sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_id in confirms.busy:
        raise HTTPException(status_code=409, detail="Session is busy")
    confirms.busy.add(session_id)

    async def events() -> AsyncIterator[str]:
        iterator = agent.run(session, body.content)
        next_event: asyncio.Task | None = None
        disconnect = asyncio.create_task(request.is_disconnected())
        try:
            while True:
                if next_event is None:
                    next_event = asyncio.create_task(anext(iterator))
                done, _ = await asyncio.wait({next_event, disconnect}, timeout=15)
                if disconnect in done and disconnect.result():
                    break
                if next_event not in done:
                    if session_id in confirms.waiting:
                        yield ": ping\n\n"
                    continue
                try:
                    event = next_event.result()
                except StopAsyncIteration:
                    break
                next_event = None
                if event["type"] == "confirm_required":
                    confirms.prepare(session_id, event["confirm_id"])
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Agent stream failed")
            session.errors.append({"message": "Internal server error", "at": time.time(),
                                   "after_message": len(session.messages)})
            yield 'data: {"type":"error","message":"Internal server error"}\n\n'
        finally:
            disconnect.cancel()
            with suppress(asyncio.CancelledError):
                await disconnect
            if next_event is not None:
                next_event.cancel()
                await asyncio.gather(next_event, return_exceptions=True)
            try:
                await iterator.aclose()
            finally:
                try:
                    # Persist even when the client disconnected (the stream is being cancelled).
                    with anyio.CancelScope(shield=True):
                        await sessions.save(session)
                except Exception:
                    logger.exception("Saving session failed")
                finally:
                    confirms.clear(session_id)

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{session_id}/confirm")
async def confirm(
    session_id: str, body: ConfirmationInput, sessions: deps.SessionsDep,
    confirms: deps.ConfirmsDep,
) -> dict:
    if await sessions.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    confirms.resolve(session_id, body.confirm_id, body.approve)
    return {"ok": True}
