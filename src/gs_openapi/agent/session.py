"""Provider-neutral chat history plus the in-memory store kept for tests.

The default store used by the HTTP server is ``gs_openapi.store.SqliteSessionStore``.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from uuid import uuid4

TITLE_CHARS = 30


@dataclass
class AgentSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    messages: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    # Built once on the first turn so every turn of a session shares one prompt.
    system_prompt: str | None = None
    title: str | None = None
    updated_at: float = field(default_factory=time.time)
    # SSE ``error`` events: {"message", "at", "after_message"} so a UI can rebuild the timeline.
    errors: list[dict] = field(default_factory=list)
    # confirm_required events and their outcome: {"confirm_id", "tool_use_id", "name", "input",
    # "summary", "decision": "approved" | "rejected" | None, "at", "after_message"}.
    confirmations: list[dict] = field(default_factory=list)


def derive_title(messages: list[dict]) -> str | None:
    """First user text message, whitespace-collapsed, first 30 characters."""
    for message in messages:
        if message.get("role") == "user" and isinstance(message.get("content"), str):
            text = " ".join(message["content"].split())
            if text:
                return text[:TITLE_CHARS]
    return None


def touch(session: AgentSession) -> None:
    """Called on every save: bump ``updated_at`` and fill a missing title."""
    session.updated_at = time.time()
    if not session.title:
        session.title = derive_title(session.messages)


def summary(session: AgentSession) -> dict:
    return {
        "session_id": session.session_id, "title": session.title,
        "created_at": session.created_at, "updated_at": session.updated_at,
        "message_count": len(session.messages),
    }


class InMemorySessionStore:
    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}
        self._lock = asyncio.Lock()

    async def create(self, title: str | None = None) -> AgentSession:
        session = AgentSession(title=title)
        async with self._lock:
            self._sessions[session.session_id] = session
        return session

    async def get(self, session_id: str) -> AgentSession | None:
        async with self._lock:
            return self._sessions.get(session_id)

    async def save(self, session: AgentSession) -> None:
        touch(session)
        async with self._lock:
            self._sessions[session.session_id] = session

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def list(self) -> list[AgentSession]:
        async with self._lock:
            return sorted(self._sessions.values(), key=lambda s: s.updated_at, reverse=True)

    async def page(
        self, page: int = 1, page_size: int = 20, include_empty: bool = False,
    ) -> tuple[list[dict], int]:
        rows = [s for s in await self.list() if include_empty or s.messages]
        start = (page - 1) * page_size
        return [summary(s) for s in rows[start:start + page_size]], len(rows)
