"""Provider-neutral Saodi (扫地僧) agent tool loop and confirmation boundary."""

import asyncio
import json
import time
from collections.abc import AsyncIterator, Callable, Iterator
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


# One budget for what a tool result may cost in the conversation (json.dumps characters). The fitted
# value is what the model sees, what the SSE ``tool_result.output`` carries and what the session stores.
TOOL_RESULT_BUDGET = 20_000
TRUNCATED_KEY = "_truncated"


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _fits(value: Any, budget: int) -> bool:
    return len(_dumps(value)) <= budget


def _object_lists(value: Any) -> Iterator[tuple[dict, str, list]]:
    """Every non-empty list held by an object key, anywhere in the value (parent, key, list)."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == TRUNCATED_KEY:
                continue
            if isinstance(item, list) and item:
                yield value, key, item
            if isinstance(item, (dict, list)):
                yield from _object_lists(item)
    elif isinstance(value, list):
        for item in value:
            yield from _object_lists(item)


def _largest_prefix(fits: Callable[[int], bool], total: int) -> int | None:
    """Largest n in [0, total] with fits(n), assuming fits is monotone; None if even 0 does not fit."""
    if not fits(0):
        return None
    low, high = 0, total
    while low < high:
        mid = (low + high + 1) // 2
        if fits(mid):
            low = mid
        else:
            high = mid - 1
    return low


def fit_tool_output(output: Any, budget: int = TOOL_RESULT_BUDGET) -> Any:
    """Return ``output`` unchanged when it fits; otherwise a valid-JSON value that fits.

    Structure first: drop items from the tail of the largest list (by serialized size) and note
    ``{"_truncated": {"field", "kept", "total", "unit": "items"}}`` on the object holding it; a root
    list is wrapped as ``{"items": [...]}``. A list that cannot keep even one item is skipped for the
    next largest (so a single oversized parent item yields to the list inside it); repeat until it
    fits. With no list left that keeps an item, fall back to a character prefix wrapped as
    ``{"_truncated": {..., "unit": "chars"}, "text": ...}``. Generic: no tool names.
    """
    text = _dumps(output)
    if len(text) <= budget:
        return output
    work: Any = json.loads(text)  # a private, JSON-normalised copy
    if isinstance(work, list):
        work = {"items": work}
    while isinstance(work, dict) and not _fits(work, budget):
        candidates = sorted(((len(_dumps(items)), parent, key, items)
                             for parent, key, items in _object_lists(work) if TRUNCATED_KEY not in parent),
                            key=lambda c: c[0], reverse=True)
        for _, parent, key, items in candidates:  # largest first; skip lists that cannot keep one item

            def keep(n: int, parent=parent, key=key, items=items) -> bool:
                parent[key] = items[:n]
                parent[TRUNCATED_KEY] = {"field": key, "kept": n, "total": len(items), "unit": "items"}
                return _fits(work, budget) or n == 0

            kept = _largest_prefix(keep, len(items)) or 0
            if kept > 0:
                keep(kept)
                break
            parent[key] = items
            del parent[TRUNCATED_KEY]
        else:
            break  # no list can keep even one item: fall back to characters
    if isinstance(work, dict) and _fits(work, budget):
        return work
    source = output if isinstance(output, str) else text

    def chars(n: int) -> bool:
        return _fits(_char_fallback(source, n), budget)

    return _char_fallback(source, _largest_prefix(chars, len(source)) or 0)


def _char_fallback(source: str, n: int) -> dict:
    return {TRUNCATED_KEY: {"field": "text", "kept": n, "total": len(source), "unit": "chars"},
            "text": source[:n]}


INTERRUPTED_RESULT = "The previous run was interrupted; the result is unknown."
# Shown to the model (it restates it in the user's language), not to the user directly.
NOT_APPROVED_RESULT = "The user did not approve this dangerous operation; the tool was not run."
NOT_RUN_RESULT = "Not run."


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
                        **({"code": event["code"]} if event.get("code") else {}),
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
                yield {"type": "error", "message": str(exc), "code": getattr(exc, "code", "provider_error")}
                return
            if end is None:
                yield {"type": "error", "message": "The model did not return a complete message",
                       "code": "incomplete_response"}
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
                    # Kept on the session so a replay can rebuild the confirmation; decision stays
                    # None if the stream ends while waiting.
                    record = {
                        "confirm_id": confirm_id, "tool_use_id": tool.id, "name": tool.name,
                        "input": tool.input, "summary": summary, "decision": None,
                        "at": time.time(), "after_message": len(session.messages),
                    }
                    session.confirmations.append(record)
                    yield {
                        "type": "confirm_required", "confirm_id": confirm_id, "tool_use_id": tool.id,
                        "name": tool.name, "input": tool.input, "summary": summary,
                    }
                    approved_now = await self.confirm_gate.ask(
                        session.session_id, confirm_id, tool.name, tool.input, summary,
                    )
                    # ConfirmGate only returns a bool: timeouts and "no confirm channel" are rejections.
                    record["decision"] = "approved" if approved_now else "rejected"
                    if not approved_now:
                        denied[tool.id] = NOT_APPROVED_RESULT
                        continue
                approved.append(tool)
            results = dict(zip(
                (tool.id for tool in approved),
                await asyncio.gather(*(self._execute(tool, session.session_id) for tool in approved)),
            ))
            blocks = []
            for tool in uses:
                output, is_error = results.get(tool.id, (denied.get(tool.id, NOT_RUN_RESULT), True))
                # One fit, three consumers: the SSE event, the stored block and (via the stored
                # block) the model all see this same value, serialized exactly once.
                fitted = fit_tool_output(output)
                yield {
                    "type": "tool_result", "id": tool.id, "name": tool.name,
                    "output": fitted, "is_error": is_error,
                }
                blocks.append({
                    "type": "tool_result", "tool_use_id": tool.id,
                    "content": _dumps(fitted), "is_error": is_error,
                })
            session.messages.append({"role": "user", "content": blocks})
            if turn == self.max_turns - 1:
                yield {"type": "error", "message": "Reached the maximum number of tool turns",
                       "code": "max_turns"}
                return


# Deprecated alias kept for one release; use SaodiAgent.
PiAgent = SaodiAgent
