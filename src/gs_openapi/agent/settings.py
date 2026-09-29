"""Agent-specific configuration and LLM backend selection."""

import logging
import os
from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .providers.base import LLMProvider

logger = logging.getLogger(__name__)

# New name -> deprecated name. The deprecated names are read for one more release.
LEGACY_ENV = {
    "SAODI_PROVIDER": "PI_AGENT_PROVIDER",
    "SAODI_MODEL": "PI_AGENT_MODEL",
    "SAODI_AUTO_APPROVE": "PI_AGENT_AUTO_APPROVE",
    "SAODI_MAX_TURNS": "PI_AGENT_MAX_TURNS",
}
_warned: set[str] = set()


def _env(name: str) -> AliasChoices:
    return AliasChoices(name.lower(), name, LEGACY_ENV[name])


def _warn_legacy_env() -> None:
    """Warn once per process for each deprecated variable actually used (name only)."""
    for new, old in LEGACY_ENV.items():
        if new not in os.environ and old in os.environ and old not in _warned:
            _warned.add(old)
            logger.warning("%s is deprecated; use %s instead (the old name goes away next release)", old, new)


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    saodi_provider: Literal["anthropic", "openai"] = Field(
        "anthropic", validation_alias=_env("SAODI_PROVIDER"))
    saodi_model: str | None = Field(None, validation_alias=_env("SAODI_MODEL"))
    saodi_auto_approve: bool = Field(False, validation_alias=_env("SAODI_AUTO_APPROVE"))
    saodi_max_turns: int = Field(12, validation_alias=_env("SAODI_MAX_TURNS"))
    saodi_context_dir: str | None = None
    saodi_context_max_chars: int = 60_000
    openai_base_url: str | None = None
    openai_api_key: str | None = None

    def __init__(self, **values):
        _warn_legacy_env()
        super().__init__(**values)

    @model_validator(mode="after")
    def set_default_model(self):
        if self.saodi_model is None:
            self.saodi_model = (
                "claude-opus-5" if self.saodi_provider == "anthropic" else "deepseek-chat"
            )
        if self.saodi_max_turns < 1:
            raise ValueError("SAODI_MAX_TURNS must be positive")
        if self.saodi_context_max_chars < 1:
            raise ValueError("SAODI_CONTEXT_MAX_CHARS must be positive")
        return self


def build_provider(settings: AgentSettings) -> LLMProvider:
    if settings.saodi_provider == "anthropic":
        from .providers.anthropic import AnthropicProvider

        return AnthropicProvider(model=settings.saodi_model)
    from .providers.openai_compat import OpenAICompatProvider

    if not settings.openai_base_url or not settings.openai_api_key:
        raise ValueError("OPENAI_BASE_URL and OPENAI_API_KEY are required for openai provider")
    return OpenAICompatProvider(
        model=settings.saodi_model,
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )
