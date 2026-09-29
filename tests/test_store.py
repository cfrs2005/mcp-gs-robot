"""SQLite persistence: sessions, tool-call log, error threads and their REST / CLI faces."""

import json

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from gs_openapi.agent.session import AgentSession
from gs_openapi.core.client import GausiumAPIClient
from gs_openapi.core.errors import GausiumAPIError
from gs_openapi.server import deps
from gs_openapi.server.app import create_app
from gs_openapi.server.routes.agent import PendingConfirms
from gs_openapi.store import CallLog, Database, SqliteSessionStore, get_call_log
from gs_openapi.store import db as store_db
from gs_openapi.store.calls import args_json, describe, redact
from gs_openapi.tools import registry
from gs_openapi.tools.registry import ToolCall, ToolSpec, call_context
from gs_openapi.v3.api import GausiumV3


def mock_v3(handler):
    class Token:
        async def get_valid_token(self):
            return "test"

        def invalidate(self):
            pass

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GausiumV3(GausiumAPIClient(http_client=http, token_manager=Token()))


def upstream_error(code, msg, trace):
    return lambda request: httpx.Response(200, json={
        "code": code, "msg": msg, "traceId": trace, "data": None})


def api_error(code, sn, trace, msg="Robot is not bound to the current user."):
    return GausiumAPIError(msg, code=code, trace_id=trace, http_status=200,
                           endpoint="v3_reports_page")


async def fail(log, tool, args, exc, ts=1000.0, source="rest"):
    await log.observe(ToolCall(tool, args, source, None, ts, 12.5, exc))


def restart():
    """Simulate a backend restart: forget every open connection."""
    for database in store_db._databases.values():
        database.close()
    store_db._databases.clear()


# --- sessions ---------------------------------------------------------------------------

async def test_sqlite_sessions_survive_restart_and_page(tmp_path):
    path = tmp_path / "s.sqlite"
    store = SqliteSessionStore(Database(path))
    first = await store.create()
    first.system_prompt = "SYS"
    first.messages += [
        {"role": "user", "content": "  列出在线机器人\n前 3 台，并且告诉我每一台的电量和当前地图名称"},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "list_robots",
                                           "input": {"page": 1}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1",
                                      "content": "[]", "is_error": False}]},
    ]
    first.errors.append({"message": "boom", "at": 1.0, "after_message": 3})
    await store.save(first)
    empty = await store.create("空")
    second = await store.create()
    second.messages.append({"role": "user", "content": "第二个"})
    await store.save(second)

    reopened = SqliteSessionStore(Database(path))  # new connection = restarted process
    loaded = await reopened.get(first.session_id)
    assert loaded is not None and loaded is not first
    assert loaded.messages == first.messages
    assert loaded.system_prompt == "SYS"
    assert loaded.errors == first.errors
    assert loaded.title == "列出在线机器人 前 3 台，并且告诉我每一台的电量和当前地图"
    assert len(loaded.title) == 30

    items, total = await reopened.page(1, 1)
    assert total == 2 and [i["session_id"] for i in items] == [second.session_id]
    items, _ = await reopened.page(2, 1)
    assert items[0]["session_id"] == first.session_id
    assert items[0]["message_count"] == 3
    items, total = await reopened.page(1, 10, include_empty=True)
    assert total == 3 and empty.session_id in {i["session_id"] for i in items}
    assert (await reopened.list())[0].session_id == second.session_id

    await reopened.delete(first.session_id)
    assert await reopened.get(first.session_id) is None


# --- redaction --------------------------------------------------------------------------

def test_redaction_is_recursive_and_truncated():
    args = {"robot_sn": "SN1", "Authorization": "Bearer x", "nested": [
        {"api_key": "k", "access_token": "t", "keep": 1}, {"deep": {"PassWord": "p"}}]}
    assert redact(args) == {"robot_sn": "SN1", "Authorization": "***", "nested": [
        {"api_key": "***", "access_token": "***", "keep": 1}, {"deep": {"PassWord": "***"}}]}
    text = args_json({"blob": "汉" * 5000, "client_secret": "s"})
    assert len(text.encode()) <= 4096 and text.endswith("…[truncated]")
    assert "\"s\"" not in text


async def test_logged_args_and_messages_hide_secrets():
    log = get_call_log()
    exc = ValueError("bad token='abc123' and password=hunter2")
    await fail(log, "some_tool", {"robot_sn": "SN", "token": "abc123"}, exc)
    thread = (await log.list_threads())[0]
    detail = await log.get_thread(thread["id"])
    dump = json.dumps(detail, ensure_ascii=False)
    assert "abc123" not in dump and "hunter2" not in dump


# --- fingerprints / classification ------------------------------------------------------

async def test_same_code_different_sn_and_trace_is_one_thread():
    log = get_call_log()
    for i, sn in enumerate(["GS000-0000-XXX-0001", "TEST00-0000-000-X102", "GS000-0000-XXX-0001"]):
        await fail(log, "list_task_reports", {"robot_sn": sn, "page": 1},
                   api_error(110003, sn, f"trace-{i}"), ts=1000.0 + i)
    threads = await log.list_threads()
    assert len(threads) == 1
    thread = threads[0]
    assert thread["count"] == 3 and thread["sn_count"] == 2
    assert thread["trace_ids"] == ["trace-2", "trace-1", "trace-0"]
    assert (thread["category"], thread["status"]) == ("account_permission", "expected")
    assert thread["code"] == "110003" and thread["first_seen"] == 1000.0
    detail = await log.get_thread(thread["id"])
    assert len(detail["calls"]) == 3 and detail["calls"][0]["trace_id"] == "trace-2"
    assert detail["calls"][0]["endpoint"] == "v3_reports_page"
    assert detail["tool_errors_total"] == 3


async def test_auto_classification():
    log = get_call_log()
    await fail(log, "get_robot_status", {"robot_sn_list": ["A-B1-C2"]},
               api_error(230003, "x", "t", "Robot columbus routing failed."))

    class Model(BaseModel):
        map_id: str

    try:
        Model.model_validate({})
    except ValidationError as exc:
        await fail(log, "list_robot_maps", {"robot_sn": "SN"}, exc)
    await fail(log, "get_robot_status", {"robot_sn_list": []},
               registry.ToolInputError("Invalid input for get_robot_status: too short"))
    await fail(log, "other", {}, RuntimeError("weird"))
    got = {t["tool"] + ":" + t["error_class"]: (t["category"], t["status"])
           for t in await log.list_threads()}
    assert got == {
        "get_robot_status:upstream": ("robot_offline", "expected"),
        "list_robot_maps:response_model": ("our_bug", "open"),
        "get_robot_status:input": ("input_error", "open"),
        "other:exception": ("unknown", "open"),
    }


async def test_response_model_errors_fold_by_model_not_by_failing_fields():
    class Report(BaseModel):
        completion: int
        brush: int = 0

    log = get_call_log()
    for sn, payload in (("SN-AA-1", {"completion": 0.9}),
                        ("SN-BB-2", {"completion": 0.8, "brush": 0.5}), ("SN-CC-3", {})):
        try:
            Report.model_validate(payload)
        except ValidationError as exc:
            await fail(log, "list_task_reports", {"robot_sn": sn}, exc)
    threads = await log.list_threads()
    assert len(threads) == 1
    assert threads[0]["count"] == 3 and threads[0]["sn_count"] == 3
    assert threads[0]["fingerprint"] == "list_task_reports|response_model|ValidationError:Report"


def test_codeless_fingerprint_normalizes_ids():
    a = describe(RuntimeError("robot GS000-0000-XXX-0001 req 3f2a9c1e-1111-2222-3333-444455556666 "
                              "took 1200ms"))
    b = describe(RuntimeError("robot TEST00-0000-000-X102 req 00000000-aaaa-bbbb-cccc-dddddddddddd "
                              "took 87ms"))
    assert a.key == b.key == "RuntimeError:robot <sn> req <uuid> took <n>ms"


async def test_fixed_thread_reopens_on_regression():
    log = get_call_log()
    await fail(log, "t", {}, RuntimeError("boom 1"), ts=1.0)
    thread = (await log.list_threads())[0]
    patched = await log.update_thread(thread["id"], status="fixed", note="patched in v0.2.1")
    assert patched["status"] == "fixed" and patched["note"] == "patched in v0.2.1"
    await fail(log, "t", {}, RuntimeError("boom 2"), ts=2.0)
    again = (await log.list_threads())[0]
    assert again["id"] == thread["id"] and again["count"] == 2
    assert again["status"] == "open" and again["reopened_at"] == 2.0
    await log.update_thread(thread["id"], status="wontfix")
    await fail(log, "t", {}, RuntimeError("boom 3"), ts=3.0)
    assert (await log.list_threads())[0]["status"] == "wontfix"
    with pytest.raises(ValueError):
        await log.update_thread(thread["id"], status="bogus")


# --- the single choke point -------------------------------------------------------------

async def test_invoke_records_success_and_failure_with_source():
    from gs_openapi.store import install_call_log

    install_call_log()

    class In(BaseModel):
        robot_sn: str

    class Out(BaseModel):
        needed: int

    async def broken(v3, args):
        return Out.model_validate({})

    spec = ToolSpec("_test_broken", "t", In, broken)
    registry.REGISTRY[spec.name] = spec
    try:
        with call_context("agent", "sess-1"):
            await registry.invoke("describe_work_state", {"work_state": 0}, None)
            with pytest.raises(ValidationError):
                await registry.invoke("_test_broken", {"robot_sn": "SN"}, None)
        with pytest.raises(KeyError):
            await registry.invoke("_no_such_tool", {}, None)
    finally:
        registry.REGISTRY.pop(spec.name)
    log = get_call_log()
    rows = log.db.sync(lambda c: [dict(r) for r in c.execute(
        "SELECT tool, source, session_id, status, msg FROM tool_calls ORDER BY id")])
    assert [(r["tool"], r["source"], r["session_id"], r["status"]) for r in rows] == [
        ("describe_work_state", "agent", "sess-1", "ok"),
        ("_test_broken", "agent", "sess-1", "error"),
        ("_no_such_tool", "unknown", None, "error"),
    ]
    assert rows[0]["msg"] is None  # never the response body
    categories = {t["tool"]: t["category"] for t in await log.list_threads()}
    assert categories == {"_test_broken": "our_bug", "_no_such_tool": "input_error"}


# --- REST -------------------------------------------------------------------------------

@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_error_thread_routes_require_key_and_fold_rest_calls(client, app, monkeypatch):
    monkeypatch.setenv("GS_SERVER_API_KEY", "k")
    key = {"X-API-Key": "k"}
    for url in ("/api/v1/errors/threads", "/api/v1/errors/threads/1", "/api/v1/agent/sessions"):
        assert (await client.get(url)).status_code == 401
    assert (await client.patch("/api/v1/errors/threads/1", json={})).status_code == 401
    traces = iter(["trace-a", "trace-b"])
    app.dependency_overrides[deps.get_v3] = lambda: mock_v3(
        lambda request: upstream_error(110003, "Robot is not bound to the current user.",
                                       next(traces))(request))
    for sn in ("SN-AA-1", "SN-BB-2"):
        response = await client.post("/api/v1/tools/list_task_reports",
                                     json={"robot_sn": sn}, headers=key)
        assert response.status_code == 502
    listed = (await client.get("/api/v1/errors/threads", headers=key)).json()["items"]
    assert len(listed) == 1
    thread = listed[0]
    assert thread["count"] == 2 and thread["sn_count"] == 2
    assert (thread["category"], thread["status"]) == ("account_permission", "expected")
    detail = (await client.get(f"/api/v1/errors/threads/{thread['id']}", headers=key)).json()
    assert [c["source"] for c in detail["calls"]] == ["rest", "rest"]
    assert detail["calls"][0]["endpoint"] and detail["calls"][0]["http_status"] == 200
    assert (await client.get("/api/v1/errors/threads?status=open", headers=key)).json() == {
        "items": []}
    assert (await client.get("/api/v1/errors/threads?status=nope", headers=key)).status_code == 422
    patched = await client.patch(f"/api/v1/errors/threads/{thread['id']}",
                                 json={"category": "upstream", "note": "账号侧"}, headers=key)
    assert patched.status_code == 200
    assert (patched.json()["category"], patched.json()["note"]) == ("upstream", "账号侧")
    assert (await client.patch(f"/api/v1/errors/threads/{thread['id']}",
                               json={"status": "bad"}, headers=key)).status_code == 422
    assert (await client.get("/api/v1/errors/threads/999", headers=key)).status_code == 404


class EchoAgent:
    async def run(self, session, text):
        session.messages.append({"role": "user", "content": text})
        session.messages.append({"role": "assistant", "content": [
            {"type": "text", "text": f"echo {len(session.messages)}"}]})
        yield {"type": "done", "message_id": "m", "usage": {}}


async def test_sessions_persist_across_backend_restart(monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)

    def fresh_client():
        application = create_app()
        application.dependency_overrides[deps.get_agent] = lambda: EchoAgent()
        application.dependency_overrides[deps.get_confirms] = PendingConfirms
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=application),
                                 base_url="http://test")

    before = fresh_client()
    session_id = (await before.post("/api/v1/agent/sessions")).json()["session_id"]
    assert (await before.get("/api/v1/agent/sessions")).json()["total"] == 0  # empty hidden
    await before.post(f"/api/v1/agent/sessions/{session_id}/messages",
                      json={"content": "列出在线机器人前 3 台"})

    restart()
    after = fresh_client()
    listed = (await after.get("/api/v1/agent/sessions")).json()
    assert listed["total"] == 1 and listed["page"] == 1
    assert listed["items"][0] | {"created_at": 0, "updated_at": 0} == {
        "session_id": session_id, "title": "列出在线机器人前 3 台", "created_at": 0,
        "updated_at": 0, "message_count": 2}
    await after.post(f"/api/v1/agent/sessions/{session_id}/messages", json={"content": "第一台的状态"})
    detail = (await after.get(f"/api/v1/agent/sessions/{session_id}")).json()
    assert detail["message_count"] == 4 and detail["errors"] == []
    assert detail["messages"][2] == {"role": "user", "content": "第一台的状态"}
    assert detail["messages"][3]["content"][0]["text"] == "echo 3"
    assert (await after.delete(f"/api/v1/agent/sessions/{session_id}")).json() == {"ok": True}
    assert (await after.get(f"/api/v1/agent/sessions/{session_id}")).status_code == 404


async def test_agent_error_events_are_kept_on_session():
    from gs_openapi.agent.core import SaodiAgent

    class Broken:
        async def stream(self, **kwargs):
            raise RuntimeError("provider down")
            yield  # pragma: no cover

    session = AgentSession(system_prompt="s")
    events = [e async for e in SaodiAgent(None, Broken()).run(session, "hi")]
    assert events == [{"type": "error", "message": "provider down", "code": "provider_error"}]
    assert session.errors[0]["message"] == "provider down"
    assert session.errors[0]["code"] == "provider_error"
    assert session.errors[0]["after_message"] == 1


async def test_cli_errors_table_and_show(capsys):
    from gs_openapi.agent.cli import main

    log: CallLog = get_call_log()
    await fail(log, "list_task_reports", {"robot_sn": "SN"}, api_error(110003, "SN", "tr-1"))
    with pytest.raises(SystemExit) as done:
        main(["errors"])
    assert done.value.code == 0
    out = capsys.readouterr().out
    assert "account_permission" in out and "110003" in out and "(1 thread(s))" in out
    with pytest.raises(SystemExit):
        main(["errors", "--status", "expected", "--json"])
    assert json.loads(capsys.readouterr().out)[0]["code"] == "110003"
    with pytest.raises(SystemExit):
        main(["errors", "show", "1"])
    assert "tr-1" in capsys.readouterr().out
    with pytest.raises(SystemExit) as missing:
        main(["errors", "show", "42"])
    assert missing.value.code == 1


async def test_live_report_shape_logs_ok_and_fixed_thread_stays_fixed(client, app, monkeypatch):
    from test_models import LIVE_TASK_REPORT

    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    log = get_call_log()

    class Report(BaseModel):
        completion: int

    try:
        Report.model_validate({"completion": 0.5})
    except ValidationError as exc:
        await fail(log, "list_task_reports", {"robot_sn": "TEST00-0000-000-X000"}, exc)
    thread = (await log.list_threads())[0]
    await log.update_thread(thread["id"], status="fixed", note="float percentages")
    app.dependency_overrides[deps.get_v3] = lambda: mock_v3(lambda request: httpx.Response(
        200, json={"code": 0, "data": {"count": 1, "page": 1, "pagesize": 20,
                                       "robotTaskReports": [LIVE_TASK_REPORT]}}))
    response = await client.post("/api/v1/tools/list_task_reports",
                                 json={"robot_sn": "TEST00-0000-000-X000"})
    assert response.status_code == 200
    assert response.json()["result"]["robotTaskReports"][0]["completionPercentage"] == 0.91
    last = log.db.sync(lambda c: dict(c.execute(
        "SELECT status, thread_id FROM tool_calls ORDER BY id DESC LIMIT 1").fetchone()))
    assert last == {"status": "ok", "thread_id": None}
    assert (await log.list_threads())[0]["status"] == "fixed"
