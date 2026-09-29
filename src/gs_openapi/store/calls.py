"""Tool-call log and error threads (failures folded by fingerprint).

Every ``registry.invoke`` outcome becomes one ``tool_calls`` row. Failures are also folded
into an ``error_threads`` row keyed by ``tool | error_class | key`` so the same problem hit
with different SNs / traceIds shows up as one thread with a growing count.
"""

from __future__ import annotations

import asyncio
import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from ..core.errors import GausiumAPIError, GausiumError
from ..tools.registry import ToolCall, ToolInputError
from .db import Database

ARGS_MAX_BYTES = 4096
MSG_MAX = 1000
TRACE_KEEP = 5
SN_KEEP = 100
STATUSES = ("open", "expected", "fixed", "wontfix")
CATEGORIES = ("our_bug", "account_permission", "robot_offline", "upstream", "input_error", "unknown")
# code -> (category, status) for errors that are known account/robot-side conditions.
KNOWN_CODES = {"110003": ("account_permission", "expected"), "230003": ("robot_offline", "expected")}
CLASS_CATEGORY = {"response_model": "our_bug", "input": "input_error"}

SECRET_KEY = re.compile(r"token|secret|key|password|authorization", re.IGNORECASE)
_SECRET_PAIR = re.compile(
    r"""(['"]?[\w-]*(?:token|secret|key|password|authorization)[\w-]*['"]?\s*[:=]\s*)(['"]?)[^'",}\s]+""",
    re.IGNORECASE)
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
_HEX = re.compile(r"\b[0-9a-f]{16,}\b", re.IGNORECASE)
_SN = re.compile(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]{2,}){2,}\b")
_NUM = re.compile(r"\d+")


def redact(value: Any) -> Any:
    """Deep copy with the value of every secret-looking key replaced by ``***``."""
    if isinstance(value, dict):
        return {k: "***" if SECRET_KEY.search(str(k)) else redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    return value


def args_json(args: Any) -> str:
    # Key-based redaction, then mask ``key=value`` secrets typed into free-text args.
    text = scrub(json.dumps(redact(args), ensure_ascii=False, separators=(",", ":"), default=str))
    raw = text.encode()
    if len(raw) <= ARGS_MAX_BYTES:
        return text
    marker = "…[truncated]"
    return raw[:ARGS_MAX_BYTES - len(marker.encode())].decode(errors="ignore") + marker


def scrub(text: str) -> str:
    """Mask ``key=value`` / ``'key': 'value'`` secrets that leak into exception messages."""
    return _SECRET_PAIR.sub(r"\1\2***", text)


def robot_sns(args: Any) -> list[str]:
    if not isinstance(args, dict):
        return []
    found = [args["robot_sn"]] if isinstance(args.get("robot_sn"), str) else []
    listed = args.get("robot_sn_list")
    if isinstance(listed, (list, tuple)):
        found += [sn for sn in listed if isinstance(sn, str)]
    return list(dict.fromkeys(sn for sn in found if sn))


def normalize(msg: str, sns: list[str] = ()) -> str:
    for sn in sorted(sns, key=len, reverse=True):
        msg = msg.replace(sn, "<sn>")
    msg = _UUID.sub("<uuid>", msg)
    msg = _HEX.sub("<hex>", msg)
    msg = _SN.sub("<sn>", msg)
    msg = _NUM.sub("<n>", msg)
    return " ".join(msg.split())[:200]


@dataclass
class Failure:
    error_class: str
    error_type: str
    msg: str
    code: str | None = None
    http_status: int | None = None
    trace_id: str | None = None
    endpoint: str | None = None
    key: str = ""


def _validation_error(exc: BaseException) -> ValidationError | None:
    if isinstance(exc, ValidationError):
        return exc
    return exc.__cause__ if isinstance(exc.__cause__, ValidationError) else None


def describe(exc: BaseException, sns: list[str] = ()) -> Failure:
    """Map an exception to its error class, upstream fields and fingerprint key."""
    if isinstance(exc, GausiumAPIError):
        failure = Failure("upstream", type(exc).__name__, exc.msg or str(exc),
                          None if exc.code is None else str(exc.code),
                          exc.http_status, exc.trace_id, exc.endpoint)
    elif isinstance(exc, (ToolInputError, KeyError)):
        failure = Failure("input", type(exc).__name__, str(exc))
    elif isinstance(exc, ValidationError):
        failure = Failure("response_model", type(exc).__name__, str(exc))
    elif isinstance(exc, GausiumError):
        failure = Failure("upstream", type(exc).__name__, str(exc),
                          trace_id=getattr(exc, "trace_id", None))
    else:
        failure = Failure("exception", type(exc).__name__, str(exc))
    failure.msg = scrub(failure.msg)[:MSG_MAX]
    if failure.code:
        failure.key = failure.code
    elif failure.error_class == "response_model":
        # Which fields fail depends on the payload; the fix point is the model, so fold by it.
        failure.key = f"{failure.error_type}:{exc.title}"
    elif (validation := _validation_error(exc)) is not None:
        locs = sorted({".".join("*" if isinstance(p, int) else str(p) for p in err["loc"])
                       + ":" + err["type"] for err in validation.errors()})
        failure.key = f"{failure.error_type}:{','.join(locs)}"[:300]
    else:
        failure.key = f"{failure.error_type}:{normalize(failure.msg, sns)}"
    return failure


def classify(failure: Failure) -> tuple[str, str]:
    """Auto (category, status) for a brand-new thread."""
    if failure.code in KNOWN_CODES:
        return KNOWN_CODES[failure.code]
    return CLASS_CATEGORY.get(failure.error_class, "unknown"), "open"


def _thread_id(conn: sqlite3.Connection, tool: str, failure: Failure, ts: float,
               sns: list[str]) -> int:
    fingerprint = f"{tool}|{failure.error_class}|{failure.key}"
    row = conn.execute("SELECT id, status, trace_ids FROM error_threads WHERE fingerprint=?",
                       (fingerprint,)).fetchone()
    traces = [failure.trace_id] if failure.trace_id else []
    if row is None:
        category, status = classify(failure)
        thread_id = conn.execute(
            "INSERT INTO error_threads (fingerprint, tool, error_class, code, sample_msg, "
            "first_seen, last_seen, count, trace_ids, status, category) "
            "VALUES (?,?,?,?,?,?,?,1,?,?,?)",
            (fingerprint, tool, failure.error_class, failure.code, failure.msg, ts, ts,
             json.dumps(traces), status, category)).lastrowid
    else:
        thread_id = row["id"]
        traces = (traces + [t for t in json.loads(row["trace_ids"]) if t not in traces])[:TRACE_KEEP]
        regressed = row["status"] == "fixed"
        conn.execute(
            "UPDATE error_threads SET count=count+1, first_seen=MIN(first_seen, ?), "
            "last_seen=MAX(last_seen, ?), trace_ids=?, "
            "status=CASE WHEN ? THEN 'open' ELSE status END, "
            "reopened_at=CASE WHEN ? THEN ? ELSE reopened_at END WHERE id=?",
            (ts, ts, json.dumps(traces), regressed, regressed, ts, thread_id))
    conn.executemany("INSERT OR IGNORE INTO error_thread_sns (thread_id, sn) VALUES (?, ?)",
                     [(thread_id, sn) for sn in sns[:SN_KEEP]])
    return thread_id


def write_call(conn: sqlite3.Connection, *, tool: str, args: Any, source: str,
               session_id: str | None, ts: float, duration_ms: float | None,
               failure: Failure | None) -> int:
    sns = robot_sns(args)
    thread_id = _thread_id(conn, tool, failure, ts, sns) if failure else None
    f = failure or Failure("", "", "")
    conn.execute(
        "INSERT INTO tool_calls (ts, source, session_id, tool, args, robot_sn, duration_ms, "
        "status, http_status, code, msg, trace_id, endpoint, error_type, thread_id) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ts, source, session_id, tool, args_json(args), ",".join(sns)[:1000] or None,
         duration_ms, "error" if failure else "ok", f.http_status, f.code,
         f.msg or None, f.trace_id, f.endpoint, f.error_type or None, thread_id))
    return thread_id or 0


def _thread(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["trace_ids"] = json.loads(data["trace_ids"])
    return data


_THREAD_SELECT = ("SELECT t.*, (SELECT COUNT(*) FROM error_thread_sns s WHERE s.thread_id=t.id) "
                  "AS sn_count FROM error_threads t")


class CallLog:
    """Async facade used by the registry observer, the REST routes and the CLI."""

    def __init__(self, db: Database):
        self.db = db

    async def observe(self, call: ToolCall) -> None:
        sns = robot_sns(call.args)
        failure = describe(call.error, sns) if call.error is not None else None
        await self.db.run(lambda conn: write_call(
            conn, tool=call.tool, args=call.args, source=call.source,
            session_id=call.session_id, ts=call.started_at, duration_ms=call.duration_ms,
            failure=failure), write=True)

    def list_threads_sync(self, status: str | None = None, category: str | None = None,
                          limit: int = 100) -> list[dict]:
        clauses, params = [], []
        for column, value in (("status", status), ("category", category)):
            if value:
                clauses.append(f"t.{column}=?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.db.sync(lambda conn: conn.execute(
            f"{_THREAD_SELECT}{where} ORDER BY t.last_seen DESC LIMIT ?",
            (*params, limit)).fetchall())
        return [_thread(row) for row in rows]

    def get_thread_sync(self, thread_id: int, calls: int = 20) -> dict | None:
        def query(conn: sqlite3.Connection):
            row = conn.execute(f"{_THREAD_SELECT} WHERE t.id=?", (thread_id,)).fetchone()
            if row is None:
                return None
            data = _thread(row)
            data["calls"] = [dict(r) for r in conn.execute(
                "SELECT * FROM tool_calls WHERE thread_id=? ORDER BY ts DESC, id DESC LIMIT ?",
                (thread_id, calls)).fetchall()]
            total, errors = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(status='error'), 0) FROM tool_calls WHERE tool=?",
                (data["tool"],)).fetchone()
            data["tool_calls_total"], data["tool_errors_total"] = total, errors
            return data
        return self.db.sync(query)

    def update_thread_sync(self, thread_id: int, *, status: str | None = None,
                           category: str | None = None, note: str | None = None) -> dict | None:
        if status is not None and status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        if category is not None and category not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
        fields = {k: v for k, v in (("status", status), ("category", category), ("note", note))
                  if v is not None}

        def update(conn: sqlite3.Connection) -> bool:
            if not conn.execute("SELECT 1 FROM error_threads WHERE id=?", (thread_id,)).fetchone():
                return False
            if fields:
                assignments = ", ".join(f"{k}=?" for k in fields)
                conn.execute(f"UPDATE error_threads SET {assignments} WHERE id=?",
                             (*fields.values(), thread_id))
            return True
        if not self.db.sync(update, write=True):
            return None
        thread = self.get_thread_sync(thread_id, calls=0)
        thread.pop("calls", None)
        return thread

    async def list_threads(self, **kwargs) -> list[dict]:
        return await asyncio.to_thread(self.list_threads_sync, **kwargs)

    async def get_thread(self, thread_id: int) -> dict | None:
        return await asyncio.to_thread(self.get_thread_sync, thread_id)

    async def update_thread(self, thread_id: int, **fields) -> dict | None:
        return await asyncio.to_thread(self.update_thread_sync, thread_id, **fields)
