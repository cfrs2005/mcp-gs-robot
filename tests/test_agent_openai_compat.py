"""OpenAI-compatible streamed tool-call assembly without network access."""

import json

import httpx

from gs_openapi.agent.providers.base import MessageEnd, TextDelta, ToolUse
from gs_openapi.agent.providers.openai_compat import OpenAICompatProvider, to_provider_messages


async def test_split_tool_arguments_and_history_round_trip():
    lines = [
        {"choices": [{"delta": {"content": "查看"}, "finish_reason": None}]},
        {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "c1", "type": "function",
            "function": {"name": "start_task", "arguments": '{"robot_sn":"R1",'}}]},
            "finish_reason": None}]},
        {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {
            "arguments": '"fusion_task_id":"F1"}'}}]}, "finish_reason": "tool_calls"}]},
        {"choices": [], "usage": {"total_tokens": 42}},
    ]
    history = [
        {"role": "user", "content": "启动"},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "old", "name": "status",
            "input": {"robot_sn": "R1"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "old",
            "content": '{"ok":true}'}]},
    ]

    def handler(request):
        assert request.url.path == "/v1/chat/completions"
        payload = json.loads(request.content)
        assert payload["stream"] is True
        assert payload["messages"][2]["tool_calls"][0]["id"] == "old"
        assert payload["messages"][3] == {
            "role": "tool", "tool_call_id": "old", "content": '{"ok":true}',
        }
        assert payload["tools"] == [{"type": "function"}]
        return httpx.Response(200, text="\n".join(
            f"data: {json.dumps(line)}\n" for line in lines
        ) + "data: [DONE]\n\n", headers={"content-type": "text/event-stream"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatProvider("deepseek-chat", "https://example.test/v1", "dummy", client)
        events = [event async for event in provider.stream(
            system="system", messages=history, tools=[{"type": "function"}],
        )]
    assert isinstance(events[0], TextDelta) and events[0].text == "查看"
    assert isinstance(events[1], ToolUse)
    assert events[1].input == {"robot_sn": "R1", "fusion_task_id": "F1"}
    assert isinstance(events[2], MessageEnd)
    assert events[2].usage == {"total_tokens": 42}
    assert events[2].assistant_content["tool_calls"][0]["function"]["name"] == "start_task"
    neutral = [
        {"role": "assistant", "content": [
            {"type": "text", "text": "查看"},
            {"type": "tool_use", "id": events[1].id, "name": events[1].name,
             "input": events[1].input},
        ]},
    ]
    round_trip = to_provider_messages(neutral)[0]["tool_calls"][0]
    original = events[2].assistant_content["tool_calls"][0]
    assert round_trip["id"] == original["id"]
    assert json.loads(round_trip["function"]["arguments"]) == json.loads(
        original["function"]["arguments"]
    )
