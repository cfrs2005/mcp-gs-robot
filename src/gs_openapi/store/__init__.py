"""Local persistence (stdlib sqlite3): agent sessions, tool-call log, error threads.

Database file: ``$SAODI_DATA_DIR/saodi.sqlite`` (default ``~/.saodi/saodi.sqlite``).
"""

from ..tools.registry import ToolCall, add_call_observer
from .calls import CATEGORIES, STATUSES, CallLog
from .db import Database, default_data_dir, default_db_path, get_database
from .sessions import SqliteSessionStore


def get_call_log() -> CallLog:
    return CallLog(get_database())


async def observe_call(call: ToolCall) -> None:
    """Registry observer; the DB path is resolved per call so tests can redirect it."""
    await get_call_log().observe(call)


def install_call_log() -> None:
    """Record every ``registry.invoke`` into the local DB (idempotent)."""
    add_call_observer(observe_call)


__all__ = [
    "CATEGORIES", "STATUSES", "CallLog", "Database", "SqliteSessionStore", "default_data_dir",
    "default_db_path", "get_call_log", "get_database", "install_call_log", "observe_call",
]
