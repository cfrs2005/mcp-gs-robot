"""Provider-neutral Saodi (扫地僧) agent tool loop and confirmation boundary."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Any, Protocol, TypedDict
from uuid import uuid4

from ..tools.registry import REGISTRY, call_context, invoke, to_anthropic_tools, to_openai_tools
from ..v3.api import GausiumV3
from .prompts import build_system_prompt
from .providers.base import LLMProvider, MessageEnd, TextDelta, ToolUse
from .session import AgentSession


class AgentEvent(TypedDict, total=False):
    type: str
    text: str
    id: str
    name: str
    input: dict
    output: Any
    is_error: bool
    confirm_id: str
    summary: str
    message_id: str
    usage: dict
    message: str


class ConfirmGate(Protocol):
    async def ask(
        self, session_id: str, confirm_id: str, name: str, input: dict, summary: str
    ) -> bool: ...


class _DenyGate:
    async def ask(
        self, session_id: str, confirm_id: str, name: str, input: dict, summary: str
    ) -> bool:
        return False


def _neutral_content(content: list[dict] | dict) -> list[dict]:
    if isinstance(content, list):
        return content
    blocks = []
    if content.get("content"):
        blocks.append({"type": "text", "text": content["content"]})
    for call in content.get("tool_calls", []):
        blocks.append({
            "type": "tool_use", "id": call["id"], "name": call["function"]["name"],
            "input": json.loads(call["function"]["arguments"]),
        })
    return blocks


def _tool_content(output: Any) -> str:
    text = json.dumps(output, ensure_ascii=False, default=str)
    return text if len(text) <= 20_000 else text[:20_000] + "…[结果已截断]"


INTERRUPTED_RESULT = "上次执行被中断，结果未知"


def close_dangling_tool_uses(messages: list[dict]) -> bool:
    """If the history ends in an assistant tool_use with no tool_result (client disconnected
    mid-run), append an ``is_error`` result for each so providers accept the next turn."""
    if not messages or messages[-1].get("role") != "assistant":
        return False
    content = messages[-1].get("content")
    ids = [b["id"] for b in content if isinstance(b, dict) and b.get("type") == "tool_use"] \
        if isinstance(content, list) else []
    if not ids:
        return False
    messages.append({"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tool_id, "content": INTERRUPTED_RESULT,
         "is_error": True} for tool_id in ids]})
    return True


class SaodiAgent:
    def __init__(
        self, v3: GausiumV3, provider: LLMProvider, *, auto_approve: bool = False,
        max_turns: int = 12, confirm_gate: ConfirmGate | None = None,
    ):
        if max_turns < 1:
            raise ValueError("max_turns must be positive")
        self.v3 = v3
        self.provider = provider
        self.auto_approve = auto_approve
        self.max_turns = max_turns
        self.confirm_gate = confirm_gate or _DenyGate()

    async def _execute(self, tool: ToolUse, session_id: str) -> tuple[Any, bool]:
        try:
            with call_context("agent", session_id):
                return await invoke(tool.name, tool.input, self.v3), False
        except Exception as exc:  # noqa: BLE001 - tool handlers are untrusted boundaries
            return str(exc), True

    async def run(self, session: AgentSession, user_text: str) -> AsyncIterator[AgentEvent]:
        """Run one user turn; ``error`` events are also kept on ``session.errors``."""
        async with aclosing(self._run(session, user_text)) as events:
            async for event in events:
                if event["type"] == "error":
                    session.errors.append({
                        "message": event["message"], "at": time.time(),
                        "after_message": len(session.messages),
                    })
                yield event

    async def _run(self, session: AgentSession, user_text: str) -> AsyncIterator[AgentEvent]:
        if session.system_prompt is None:
            session.system_prompt = build_system_prompt()
        close_dangling_tool_uses(session.messages)
        session.messages.append({"role": "user", "content": user_text})
        tools = (to_openai_tools() if getattr(self.provider, "tool_format", "anthropic") == "openai"
                 else to_anthropic_tools())
        for turn in range(self.max_turns):
            uses: list[ToolUse] = []
            end: MessageEnd | None = None
            try:
                async for event in self.provider.stream(
                    system=session.system_prompt, messages=session.messages, tools=tools,
                ):
                    if isinstance(event, TextDelta):
                        yield {"type": "text_delta", "text": event.text}
                    elif isinstance(event, ToolUse):
                        uses.append(event)
                    elif isinstance(event, MessageEnd):
                        end = event
            except Exception as exc:  # noqa: BLE001 - report provider failures as SSE errors
                yield {"type": "error", "message": str(exc)}
                return
            if end is None:
                yield {"type": "error", "message": "模型未返回完整消息"}
                return
            session.messages.append({"role": "assistant", "content": _neutral_content(end.assistant_content)})
            if end.stop_reason == "refusal" or not uses:
                yield {"type": "done", "message_id": str(uuid4()), "usage": end.usage}
                return

            for tool in uses:
                yield {"type": "tool_call", "id": tool.id, "name": tool.name, "input": tool.input}
            approved: list[ToolUse] = []
            denied: dict[str, str] = {}
            for tool in uses:
                if tool.name in REGISTRY and REGISTRY[tool.name].dangerous and not self.auto_approve:
                    summary = " ".join(f"{key}={value}" for key, value in tool.input.items())
                    summary = f"{tool.name} {summary}".strip()
                    confirm_id = str(uuid4())
                    yield {
                        "type": "confirm_required", "confirm_id": confirm_id,
                        "name": tool.name, "input": tool.input, "summary": summary,
                    }
                    if not await self.confirm_gate.ask(
                        session.session_id, confirm_id, tool.name, tool.input, summary,
                    ):
                        denied[tool.id] = "用户未批准危险操作，工具未执行。"
                        continue
                approved.append(tool)
            results = dict(zip(
                (tool.id for tool in approved),
                await asyncio.gather(*(self._execute(tool, session.session_id) for tool in approved)),
            ))
            blocks = []
            for tool in uses:
                output, is_error = results.get(tool.id, (denied.get(tool.id, "未执行"), True))
                safe_output = _tool_content(output)
                if len(safe_output) > 20_000:
                    output = safe_output
                yield {
                    "type": "tool_result", "id": tool.id, "name": tool.name,
                    "output": output, "is_error": is_error,
                }
                blocks.append({
                    "type": "tool_result", "tool_use_id": tool.id,
                    "content": _tool_content(output), "is_error": is_error,
                })
            session.messages.append({"role": "user", "content": blocks})
            if turn == self.max_turns - 1:
                yield {"type": "error", "message": "已达到最大工具轮数"}
                return


# Deprecated alias kept for one release; use SaodiAgent.
PiAgent = SaodiAgent
