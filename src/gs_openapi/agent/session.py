"""In-memory, provider-neutral chat history."""

import asyncio
import time
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class AgentSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    messages: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class InMemorySessionStore:
    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}
        self._lock = asyncio.Lock()

    async def create(self, title: str | None = None) -> AgentSession:
        session = AgentSession()
        async with self._lock:
            self._sessions[session.session_id] = session
        return session

    async def get(self, session_id: str) -> AgentSession | None:
        async with self._lock:
            return self._sessions.get(session_id)

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def list(self) -> list[AgentSession]:
        async with self._lock:
            return list(self._sessions.values())
