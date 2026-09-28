"""OpenAI-compatible chat completions over streamed SSE."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .base import AgentProviderError, MessageEnd, ProviderEvent, TextDelta, ToolUse


def to_provider_messages(history: list[dict]) -> list[dict]:
    """Convert neutral Anthropic-shaped blocks to OpenAI chat messages."""
    converted = []
    for message in history:
        content = message["content"]
        if isinstance(content, str):
            converted.append({"role": message["role"], "content": content})
            continue
        if message["role"] == "assistant":
            text = "\n".join(block["text"] for block in content if block["type"] == "text")
            calls = [
                {"id": block["id"], "type": "function", "function": {
                    "name": block["name"], "arguments": json.dumps(block["input"], ensure_ascii=False),
                }}
                for block in content if block["type"] == "tool_use"
            ]
            assistant = {"role": "assistant", "content": text or None}
            if calls:
                assistant["tool_calls"] = calls
            converted.append(assistant)
        else:
            for block in content:
                if block["type"] == "tool_result":
                    value = block["content"]
                    converted.append({
                        "role": "tool", "tool_call_id": block["tool_use_id"],
                        "content": value if isinstance(value, str) else json.dumps(value, ensure_ascii=False),
                    })
                elif block["type"] == "text":
                    converted.append({"role": "user", "content": block["text"]})
    return converted


class OpenAICompatProvider:
    tool_format = "openai"

    def __init__(
        self, model: str, base_url: str, api_key: str, client: httpx.AsyncClient | None = None
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = client

    async def stream(
        self, *, system: str, messages: list[dict], tools: list[dict]
    ) -> AsyncIterator[ProviderEvent]:
        client = self.client or httpx.AsyncClient(timeout=120)
        calls: dict[int, dict[str, Any]] = {}
        text_parts: list[str] = []
        usage: dict = {}
        stop_reason = None
        try:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model, "messages": [
                        {"role": "system", "content": system}, *to_provider_messages(messages),
                    ], "tools": tools, "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    usage = chunk.get("usage") or usage
                    for choice in chunk.get("choices", []):
                        stop_reason = choice.get("finish_reason") or stop_reason
                        delta = choice.get("delta") or {}
                        if delta.get("content"):
                            text_parts.append(delta["content"])
                            yield TextDelta(delta["content"])
                        for part in delta.get("tool_calls", []):
                            call = calls.setdefault(part["index"], {"id": "", "name": "", "args": ""})
                            call["id"] += part.get("id") or ""
                            function = part.get("function") or {}
                            call["name"] += function.get("name") or ""
                            call["args"] += function.get("arguments") or ""
            openai_calls = []
            for index in sorted(calls):
                call = calls[index]
                args = json.loads(call["args"] or "{}")
                openai_calls.append({
                    "id": call["id"], "type": "function", "function": {
                        "name": call["name"], "arguments": call["args"],
                    },
                })
                yield ToolUse(id=call["id"], name=call["name"], input=args)
            assistant = {"role": "assistant", "content": "".join(text_parts) or None}
            if openai_calls:
                assistant["tool_calls"] = openai_calls
            yield MessageEnd(stop_reason=stop_reason, usage=usage, assistant_content=assistant)
        except (httpx.HTTPError, ValueError) as exc:
            raise AgentProviderError(f"OpenAI 兼容服务请求失败: {exc}") from exc
        finally:
            if self.client is None:
                await client.aclose()
