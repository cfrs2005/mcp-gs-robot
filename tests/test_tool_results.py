"""Structure-aware tool-result truncation and persisted confirmations (no upstream calls)."""

import json
import sqlite3

import httpx
import pytest

from gs_openapi.agent.core import TOOL_RESULT_BUDGET, SaodiAgent, fit_tool_output
from gs_openapi.agent.providers.base import MessageEnd, TextDelta, ToolUse
from gs_openapi.agent.session import AgentSession
from gs_openapi.server import deps
from gs_openapi.server.app import create_app
from gs_openapi.store import Database, SqliteSessionStore
from gs_openapi.store import db as store_db


def report(i: int) -> dict:
    return {"id": f"r{i}", "displayName": "天台", "actualCleaningAreaSquareMeter": 400.0 + i,
            "note": "x" * 900, "subTasks": [{"mapId": "m", "mapName": "天台"}]}


def size(value) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str))


# --- fit_tool_output ------------------------------------------------------------------------

def test_small_result_is_returned_unchanged():
    value = {"list": [{"robotSn": "R1"}], "count": 1}
    assert fit_tool_output(value) is value
    assert fit_tool_output("short text") == "short text"


def test_large_list_is_cut_from_the_tail_with_metadata():
    value = {"count": 14671, "page": 1, "robotTaskReports": [report(i) for i in range(40)]}
    fitted = fit_tool_output(value)
    text = json.dumps(fitted, ensure_ascii=False)
    assert size(fitted) <= TOOL_RESULT_BUDGET and json.loads(text) == fitted
    meta = fitted["_truncated"]
    assert meta["field"] == "robotTaskReports" and meta["total"] == 40 and meta["unit"] == "items"
    assert 0 < meta["kept"] < 40
    assert fitted["robotTaskReports"] == value["robotTaskReports"][:meta["kept"]]  # head kept, in order
    assert fitted["count"] == 14671  # siblings untouched
    # Largest prefix that fits: one more item would not.
    more = {**fitted, "robotTaskReports": value["robotTaskReports"][:meta["kept"] + 1]}
    more["_truncated"] = {**meta, "kept": meta["kept"] + 1}
    assert size(more) > TOOL_RESULT_BUDGET
    assert len(value["robotTaskReports"]) == 40  # the input is not mutated


def test_nested_list_gets_metadata_on_its_own_object():
    value = {"maps": [{"mapId": "m1", "positions": [{"name": "p" * 200, "gridX": str(i)} for i in range(200)]}]}
    fitted = fit_tool_output(value)
    assert size(fitted) <= TOOL_RESULT_BUDGET
    holder = fitted["maps"][0]
    assert holder["_truncated"]["field"] == "positions" and holder["_truncated"]["total"] == 200
    assert len(holder["positions"]) == holder["_truncated"]["kept"]


def test_root_list_is_wrapped_as_items():
    fitted = fit_tool_output([report(i) for i in range(40)])
    assert fitted["_truncated"]["field"] == "items" and len(fitted["items"]) == fitted["_truncated"]["kept"]
    assert size(fitted) <= TOOL_RESULT_BUDGET


@pytest.mark.parametrize("value", [{"data": "x" * 50_000}, "y" * 50_000])
def test_without_a_list_it_falls_back_to_characters_as_valid_json(value):
    fitted = fit_tool_output(value)
    assert size(fitted) <= TOOL_RESULT_BUDGET
    meta = fitted["_truncated"]
    assert meta["unit"] == "chars" and meta["field"] == "text" and meta["kept"] == len(fitted["text"])
    source = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    assert meta["total"] == len(source) and source.startswith(fitted["text"])


def test_list_of_huge_items_moves_on_then_falls_back():
    # Even one item exceeds the budget: the list is emptied, nothing else to cut, so text fallback.
    fitted = fit_tool_output({"list": ["z" * 30_000, "z" * 30_000]})
    assert fitted["_truncated"]["unit"] == "chars" and size(fitted) <= TOOL_RESULT_BUDGET


# --- the agent: one fit for SSE, model and storage ------------------------------------------

class FakeProvider:
    def __init__(self, *turns):
        self.turns = list(turns)
        self.messages = []

    async def stream(self, *, system, messages, tools):
        self.messages.append(json.loads(json.dumps(messages)))
        for event in self.turns.pop(0):
            yield event


def end(*blocks, stop="end_turn"):
    return MessageEnd(stop, {}, list(blocks))


def tool_turn(name, args, tool_id="t1"):
    block = {"type": "tool_use", "id": tool_id, "name": name, "input": args}
    return [ToolUse(tool_id, name, args), end(block, stop="tool_use")]


async def test_sse_model_and_store_share_one_truncation(monkeypatch):
    big = {"count": 99, "robotTaskReports": [report(i) for i in range(40)]}

    async def fake_invoke(name, args, v3):
        return big

    monkeypatch.setattr("gs_openapi.agent.core.invoke", fake_invoke)
    provider = FakeProvider(tool_turn("list_task_reports", {"robot_sn": "R1"}),
                            [TextDelta("ok"), end({"type": "text", "text": "ok"})])
    session = AgentSession(system_prompt="s")
    events = [e async for e in SaodiAgent(None, provider).run(session, "reports")]
    sse = next(e for e in events if e["type"] == "tool_result")["output"]
    stored = session.messages[2]["content"][0]["content"]
    seen_by_model = provider.messages[1][2]["content"][0]["content"]
    assert stored == seen_by_model == json.dumps(sse, ensure_ascii=False)
    assert json.loads(stored)["_truncated"]["total"] == 40  # single encoding: parses to an object


# --- confirmations ------------------------------------------------------------------------

class Gate:
    def __init__(self, approved):
        self.approved = approved

    async def ask(self, session_id, confirm_id, name, input, summary):
        return self.approved


@pytest.mark.parametrize("approved", [True, False])
async def test_confirmations_are_recorded(monkeypatch, approved):
    ran = []

    async def fake_invoke(name, args, v3):  # never reaches upstream
        ran.append(name)
        return {"requestId": "Q1", "cmdStatus": 6}

    monkeypatch.setattr("gs_openapi.agent.core.invoke", fake_invoke)
    args = {"robot_sn": "R1", "fusion_task_id": "F1"}
    provider = FakeProvider(tool_turn("start_task", args, "tu9"), [end({"type": "text", "text": "done"})])
    session = AgentSession(system_prompt="s")
    events = [e async for e in SaodiAgent(None, provider, confirm_gate=Gate(approved)).run(session, "go")]
    confirm = next(e for e in events if e["type"] == "confirm_required")
    assert confirm["tool_use_id"] == "tu9"
    [record] = session.confirmations
    assert record["confirm_id"] == confirm["confirm_id"] and record["tool_use_id"] == "tu9"
    assert record["name"] == "start_task" and record["input"] == args
    assert record["decision"] == ("approved" if approved else "rejected")
    assert record["after_message"] == 2  # user + assistant(tool_use) existed when it was asked
    assert ran == (["start_task"] if approved else [])


async def test_unanswered_confirmation_keeps_decision_null():
    class Hang:
        async def ask(self, *args):
            raise RuntimeError("stream closed")

    provider = FakeProvider(tool_turn("stop_task", {"robot_sn": "R1"}))
    session = AgentSession(system_prompt="s")
    with pytest.raises(RuntimeError):
        _ = [e async for e in SaodiAgent(None, provider, confirm_gate=Hang()).run(session, "stop")]
    assert session.confirmations[0]["decision"] is None


# --- storage ------------------------------------------------------------------------------

async def test_store_round_trips_confirmations(tmp_path):
    store = SqliteSessionStore(Database(tmp_path / "s.sqlite"))
    session = await store.create()
    session.confirmations.append({"confirm_id": "c1", "tool_use_id": "t1", "decision": "rejected"})
    await store.save(session)
    assert (await store.get(session.session_id)).confirmations == session.confirmations


def test_v1_database_is_migrated_idempotently(tmp_path):
    path = tmp_path / "old.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE sessions (id TEXT PRIMARY KEY, title TEXT, system_prompt TEXT,
            messages TEXT NOT NULL DEFAULT '[]', errors TEXT NOT NULL DEFAULT '[]',
            message_count INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL, updated_at REAL NOT NULL);
        INSERT INTO sessions VALUES ('old', 't', NULL, '[]', '[]', 0, 1, 1);
        PRAGMA user_version=1;""")
    conn.close()
    for _ in range(2):  # opening twice must not fail on the second ALTER
        database = Database(path)
        columns = {row[1] for row in database.sync(lambda c: c.execute("PRAGMA table_info(sessions)").fetchall())}
        assert "confirmations" in columns
        assert database.sync(lambda c: c.execute("PRAGMA user_version").fetchone()[0]) == 2
        database.close()


async def test_old_row_reads_as_empty_confirmations(tmp_path):
    database = Database(tmp_path / "s.sqlite")
    database.sync(lambda c: c.execute(
        "INSERT INTO sessions (id, title, messages, errors, message_count, created_at, updated_at) "
        "VALUES ('legacy', NULL, '[]', '[]', 0, 1, 1)"), write=True)
    assert (await SqliteSessionStore(database).get("legacy")).confirmations == []


async def test_get_session_route_returns_confirmations(monkeypatch, tmp_path):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    monkeypatch.setenv("SAODI_DATA_DIR", str(tmp_path))
    store_db._databases.clear()
    app = create_app()
    store = SqliteSessionStore(store_db.get_database())
    app.dependency_overrides[deps.get_sessions] = lambda: store
    session = await store.create()
    session.messages.append({"role": "user", "content": "go"})
    session.confirmations.append({"confirm_id": "c1", "tool_use_id": "t1", "name": "stop_task",
                                  "input": {}, "summary": "stop_task", "decision": "rejected",
                                  "at": 1.0, "after_message": 1})
    await store.save(session)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as client:
        body = (await client.get(f"/api/v1/agent/sessions/{session.session_id}")).json()
    assert body["confirmations"] == session.confirmations
    store_db._databases.clear()
