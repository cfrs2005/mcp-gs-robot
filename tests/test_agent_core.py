"""Pi Agent event, confirmation, and history contract tests."""

import json

import httpx
import pytest

from gs_openapi.agent.core import PiAgent
from gs_openapi.agent.providers.base import MessageEnd, TextDelta, ToolUse
from gs_openapi.agent.session import AgentSession, InMemorySessionStore
from gs_openapi.agent.settings import AgentSettings
from gs_openapi.auth.token_manager import TokenManager
from gs_openapi.core.client import GausiumAPIClient
from gs_openapi.v3.api import GausiumV3


class FakeProvider:
    def __init__(self, *turns):
        self.turns = list(turns)
        self.messages = []

    async def stream(self, *, system, messages, tools):
        self.messages.append(json.loads(json.dumps(messages)))
        for event in self.turns.pop(0):
            yield event


def end(*blocks, stop="end_turn"):
    return MessageEnd(stop, {"input_tokens": 10}, list(blocks))


def tool_turn(name="get_robot_status", args=None):
    args = args or {"robot_sn_list": ["R1"]}
    block = {"type": "tool_use", "id": "t1", "name": name, "input": args}
    return [TextDelta("查询中"), ToolUse("t1", name, args), end(block, stop="tool_use")]


def mock_v3(handler):
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token = TokenManager(client_id="c", client_secret="s", open_access_key="k", http_client=http)
    return GausiumV3(GausiumAPIClient(http_client=http, token_manager=token)), http


def status_response(request):
    if request.url.path.endswith("oauth/token"):
        return httpx.Response(200, json={"access_token": "t", "expires_in": 9999999999999,
                                         "refresh_token": "r", "token_type": "bearer"})
    assert json.loads(request.content) == {"robotSnList": ["R1"]}
    return httpx.Response(200, json={"code": 0, "msg": "ok", "data": {
        "list": [{"robotSn": "R1", "workState": 230}],
    }})


async def test_tool_loop_and_neutral_history():
    v3, http = mock_v3(status_response)
    provider = FakeProvider(tool_turn(), [TextDelta("完成"), end({"type": "text", "text": "完成"})])
    session = AgentSession()
    try:
        events = [event async for event in PiAgent(v3, provider).run(session, "查询 R1")]
        assert [event["type"] for event in events] == [
            "text_delta", "tool_call", "tool_result", "text_delta", "done",
        ]
        assert events[2]["output"]["list"][0]["work_state_name"] == "AUTO_TASKING"
        assert session.messages[0] == {"role": "user", "content": "查询 R1"}
        assert session.messages[1]["content"][0]["type"] == "tool_use"
        assert len(session.messages[2]["content"]) == 1
        assert session.messages[2]["content"][0]["tool_use_id"] == "t1"
        assert provider.messages[1] == session.messages[:-1]
        assert session.messages[-1]["role"] == "assistant"
    finally:
        await http.aclose()


class Gate:
    def __init__(self, approved):
        self.approved = approved
        self.calls = []

    async def ask(self, session_id, confirm_id, name, input, summary):
        self.calls.append((session_id, confirm_id, name, input, summary))
        return self.approved


@pytest.mark.parametrize("approved", [True, False])
async def test_confirmation(approved):
    called = []

    def handler(request):
        if request.url.path.endswith("oauth/token"):
            return status_response(request)
        called.append(request)
        return httpx.Response(200, json={"code": 0, "msg": "ok", "data": {
            "requestId": "Q1", "cmdStatus": 6,
        }})

    v3, http = mock_v3(handler)
    args = {"robot_sn": "R1", "fusion_task_id": "F1"}
    provider = FakeProvider(tool_turn("start_task", args), [end({"type": "text", "text": "收到"})])
    gate = Gate(approved)
    try:
        events = [event async for event in PiAgent(v3, provider, confirm_gate=gate).run(
            AgentSession(), "启动 R1 的 F1"
        )]
        assert [event["type"] for event in events[:4]] == [
            "text_delta", "tool_call", "confirm_required", "tool_result",
        ]
        assert "robot_sn=R1" in events[2]["summary"]
        assert gate.calls[0][1] == events[2]["confirm_id"]
        assert events[3]["is_error"] is not approved
        assert len(called) == int(approved)
        assert provider.messages[1][2]["content"][0]["is_error"] is not approved
    finally:
        await http.aclose()


async def test_max_turns_and_tool_error():
    provider = FakeProvider(tool_turn(), tool_turn())
    session = AgentSession()
    agent = PiAgent(None, provider, max_turns=1)
    events = [event async for event in agent.run(session, "查询")]
    assert events[-1] == {"type": "error", "message": "已达到最大工具轮数"}
    assert len(provider.messages) == 1
    assert events[2]["type"] == "tool_result" and events[2]["is_error"]
    assert session.messages[2]["content"][0]["is_error"]


async def test_default_gate_denies_without_invocation():
    args = {"robot_sn": "R1", "fusion_task_id": "F1"}
    provider = FakeProvider(tool_turn("start_task", args), [end({"type": "text", "text": "取消"})])
    events = [event async for event in PiAgent(None, provider).run(AgentSession(), "启动 R1")]
    assert [event["type"] for event in events] == [
        "text_delta", "tool_call", "confirm_required", "tool_result", "done",
    ]
    assert events[3]["is_error"] and "未批准" in events[3]["output"]


async def test_large_tool_output_is_truncated(monkeypatch):
    async def large_result(name, args, v3):
        return {"data": "x" * 25_000}

    monkeypatch.setattr("gs_openapi.agent.core.invoke", large_result)
    provider = FakeProvider(tool_turn(), [end({"type": "text", "text": "完成"})])
    session = AgentSession()
    events = [event async for event in PiAgent(None, provider).run(session, "查询")]
    assert events[2]["output"].endswith("[结果已截断]")
    assert len(session.messages[2]["content"][0]["content"]) < 21_000


async def test_store_and_provider_defaults(monkeypatch):
    monkeypatch.setenv("PI_AGENT_PROVIDER", "openai")
    settings = AgentSettings()
    assert settings.pi_agent_model == "deepseek-chat"
    store = InMemorySessionStore()
    created = await store.create("test")
    assert (await store.get(created.session_id)) is created
    assert await store.list() == [created]
    await store.delete(created.session_id)
    assert await store.get(created.session_id) is None
