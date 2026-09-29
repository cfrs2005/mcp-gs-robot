"""Agent-specific configuration and LLM backend selection."""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .providers.base import LLMProvider


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    pi_agent_provider: Literal["anthropic", "openai"] = "anthropic"
    pi_agent_model: str | None = None
    pi_agent_auto_approve: bool = False
    pi_agent_max_turns: int = 12
    openai_base_url: str | None = None
    openai_api_key: str | None = None

    @model_validator(mode="after")
    def set_default_model(self):
        if self.pi_agent_model is None:
            self.pi_agent_model = (
                "claude-opus-5" if self.pi_agent_provider == "anthropic" else "deepseek-chat"
            )
        if self.pi_agent_max_turns < 1:
            raise ValueError("PI_AGENT_MAX_TURNS must be positive")
        return self


def build_provider(settings: AgentSettings) -> LLMProvider:
    if settings.pi_agent_provider == "anthropic":
        from .providers.anthropic import AnthropicProvider

        return AnthropicProvider(model=settings.pi_agent_model)
    from .providers.openai_compat import OpenAICompatProvider

    if not settings.openai_base_url or not settings.openai_api_key:
        raise ValueError("OPENAI_BASE_URL and OPENAI_API_KEY are required for openai provider")
    return OpenAICompatProvider(
        model=settings.pi_agent_model,
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )
