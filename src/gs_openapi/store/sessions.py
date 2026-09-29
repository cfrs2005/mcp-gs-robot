"""SQLite-backed SessionStore: sessions survive a backend restart."""

from __future__ import annotations

import json
import sqlite3

from ..agent.session import AgentSession, touch
from .db import Database

_COLUMNS = "id, title, system_prompt, messages, errors, message_count, created_at, updated_at"


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _row(session: AgentSession) -> tuple:
    return (session.session_id, session.title, session.system_prompt, _dump(session.messages),
            _dump(session.errors), len(session.messages), session.created_at, session.updated_at)


def _session(row: sqlite3.Row) -> AgentSession:
    return AgentSession(
        session_id=row["id"], messages=json.loads(row["messages"]), created_at=row["created_at"],
        system_prompt=row["system_prompt"], title=row["title"], updated_at=row["updated_at"],
        errors=json.loads(row["errors"]),
    )


def _summary(row: sqlite3.Row) -> dict:
    return {"session_id": row["id"], "title": row["title"], "created_at": row["created_at"],
            "updated_at": row["updated_at"], "message_count": row["message_count"]}


class SqliteSessionStore:
    """``get`` returns a fresh object each time; the route saves it when a stream ends."""

    def __init__(self, db: Database):
        self.db = db

    def _upsert(self, conn: sqlite3.Connection, session: AgentSession) -> None:
        conn.execute(
            f"INSERT INTO sessions ({_COLUMNS}) VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET title=excluded.title, "
            "system_prompt=excluded.system_prompt, messages=excluded.messages, "
            "errors=excluded.errors, message_count=excluded.message_count, "
            "updated_at=excluded.updated_at",
            _row(session),
        )

    async def create(self, title: str | None = None) -> AgentSession:
        session = AgentSession(title=title)
        session.updated_at = session.created_at
        await self.db.run(lambda conn: self._upsert(conn, session), write=True)
        return session

    async def get(self, session_id: str) -> AgentSession | None:
        row = await self.db.run(lambda conn: conn.execute(
            f"SELECT {_COLUMNS} FROM sessions WHERE id=?", (session_id,)).fetchone())
        return _session(row) if row else None

    async def save(self, session: AgentSession) -> None:
        touch(session)
        await self.db.run(lambda conn: self._upsert(conn, session), write=True)

    async def delete(self, session_id: str) -> None:
        await self.db.run(
            lambda conn: conn.execute("DELETE FROM sessions WHERE id=?", (session_id,)), write=True)

    async def list(self) -> list[AgentSession]:
        rows = await self.db.run(lambda conn: conn.execute(
            f"SELECT {_COLUMNS} FROM sessions ORDER BY updated_at DESC").fetchall())
        return [_session(row) for row in rows]

    async def page(
        self, page: int = 1, page_size: int = 20, include_empty: bool = False,
    ) -> tuple[list[dict], int]:
        where = "" if include_empty else "WHERE message_count > 0"

        def query(conn: sqlite3.Connection):
            total = conn.execute(f"SELECT COUNT(*) FROM sessions {where}").fetchone()[0]
            rows = conn.execute(
                f"SELECT id, title, created_at, updated_at, message_count FROM sessions {where} "
                "ORDER BY updated_at DESC, id LIMIT ? OFFSET ?",
                (page_size, (page - 1) * page_size)).fetchall()
            return [_summary(row) for row in rows], total

        return await self.db.run(query)
