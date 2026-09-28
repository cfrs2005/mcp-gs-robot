"""Provider-independent streaming events."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol


class AgentProviderError(Exception):
    """An LLM backend could not complete a request."""


@dataclass
class TextDelta:
    text: str


@dataclass
class ToolUse:
    id: str
    name: str
    input: dict


@dataclass
class MessageEnd:
    stop_reason: str | None
    usage: dict
    assistant_content: list[dict] | dict[str, Any]


ProviderEvent = TextDelta | ToolUse | MessageEnd


class LLMProvider(Protocol):
    def stream(
        self, *, system: str, messages: list[dict], tools: list[dict]
    ) -> AsyncIterator[ProviderEvent]: ...
