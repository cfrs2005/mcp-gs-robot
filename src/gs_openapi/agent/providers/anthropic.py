"""Anthropic Messages streaming provider."""

from collections.abc import AsyncIterator

import anthropic

from .base import AgentProviderError, MessageEnd, ProviderEvent, TextDelta, ToolUse


class AnthropicProvider:
    def __init__(self, model: str, client: anthropic.AsyncAnthropic | None = None):
        self.model = model
        self.client = client or anthropic.AsyncAnthropic()

    async def stream(
        self, *, system: str, messages: list[dict], tools: list[dict]
    ) -> AsyncIterator[ProviderEvent]:
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=16000,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                tools=tools,
                thinking={"type": "adaptive"},
                messages=messages,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield TextDelta(event.delta.text)
                message = await stream.get_final_message()
            content = [block.model_dump(mode="json") for block in message.content]
            if message.stop_reason == "refusal":
                explanation = "模型拒绝了该请求。"
                yield TextDelta(explanation)
                content.append({"type": "text", "text": explanation})
            else:
                for block in message.content:
                    if block.type == "tool_use":
                        yield ToolUse(id=block.id, name=block.name, input=block.input)
            yield MessageEnd(
                stop_reason=message.stop_reason,
                usage=message.usage.model_dump(),
                assistant_content=content,
            )
        except anthropic.AuthenticationError as exc:
            raise AgentProviderError("Anthropic 认证失败，请检查 ANTHROPIC_API_KEY") from exc
        except anthropic.RateLimitError as exc:
            raise AgentProviderError("Anthropic 请求频率超限，请稍后重试") from exc
        except anthropic.APIStatusError as exc:
            raise AgentProviderError(f"Anthropic API 错误 (HTTP {exc.status_code}): {exc}") from exc
        except anthropic.APIConnectionError as exc:
            raise AgentProviderError(f"Anthropic 连接失败: {exc}") from exc
