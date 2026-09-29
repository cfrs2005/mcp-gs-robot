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
                explanation = "The model declined this request."
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
            raise AgentProviderError(
                "Anthropic authentication failed; check ANTHROPIC_API_KEY", "provider_auth") from exc
        except anthropic.RateLimitError as exc:
            raise AgentProviderError(
                "Anthropic rate limit exceeded; try again later", "provider_rate_limited") from exc
        except anthropic.APIStatusError as exc:
            raise AgentProviderError(
                f"Anthropic API error (HTTP {exc.status_code}): {exc}", "provider_http") from exc
        except anthropic.APIConnectionError as exc:
            raise AgentProviderError(
                f"Anthropic connection failed: {exc}", "provider_connection") from exc
