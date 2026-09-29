"""SQLite connection, schema and the thread hop that keeps writes off the event loop."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")

SCHEMA_VERSION = 1
SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    system_prompt TEXT,
    messages TEXT NOT NULL DEFAULT '[]',
    errors TEXT NOT NULL DEFAULT '[]',
    message_count INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_updated ON sessions(updated_at DESC);

CREATE TABLE IF NOT EXISTS error_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT NOT NULL UNIQUE,
    tool TEXT NOT NULL,
    error_class TEXT NOT NULL,
    code TEXT,
    sample_msg TEXT,
    first_seen REAL NOT NULL,
    last_seen REAL NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    trace_ids TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'open',
    category TEXT NOT NULL DEFAULT 'unknown',
    note TEXT NOT NULL DEFAULT '',
    reopened_at REAL
);
CREATE INDEX IF NOT EXISTS error_threads_last ON error_threads(last_seen DESC);

CREATE TABLE IF NOT EXISTS error_thread_sns (
    thread_id INTEGER NOT NULL,
    sn TEXT NOT NULL,
    PRIMARY KEY (thread_id, sn)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    source TEXT NOT NULL,
    session_id TEXT,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    robot_sn TEXT,
    duration_ms REAL,
    status TEXT NOT NULL,
    http_status INTEGER,
    code TEXT,
    msg TEXT,
    trace_id TEXT,
    endpoint TEXT,
    error_type TEXT,
    thread_id INTEGER
);
CREATE INDEX IF NOT EXISTS tool_calls_thread ON tool_calls(thread_id, ts DESC);
CREATE INDEX IF NOT EXISTS tool_calls_tool ON tool_calls(tool, status);
"""


def default_data_dir() -> Path:
    return Path(os.environ.get("SAODI_DATA_DIR") or "~/.saodi").expanduser()


def default_db_path() -> Path:
    return default_data_dir() / "saodi.sqlite"


class Database:
    """One shared connection guarded by a lock; WAL lets other processes read meanwhile."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        existed = self.path.exists()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        if not existed:
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA busy_timeout=5000")
            self._conn.executescript(SCHEMA)
            self._conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    def sync(self, fn: Callable[[sqlite3.Connection], T], *, write: bool = False) -> T:
        with self._lock:
            if not write:
                return fn(self._conn)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                result = fn(self._conn)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            self._conn.execute("COMMIT")
            return result

    async def run(self, fn: Callable[[sqlite3.Connection], T], *, write: bool = False) -> T:
        return await asyncio.to_thread(self.sync, fn, write=write)

    def close(self) -> None:
        with self._lock:
            self._conn.close()


_databases: dict[Path, Database] = {}
_databases_lock = threading.Lock()


def get_database(path: Path | str | None = None) -> Database:
    """Process-wide Database per file; resolves ``SAODI_DATA_DIR`` at call time."""
    resolved = Path(path or default_db_path()).expanduser().resolve()
    with _databases_lock:
        if resolved not in _databases:
            _databases[resolved] = Database(resolved)
        return _databases[resolved]
