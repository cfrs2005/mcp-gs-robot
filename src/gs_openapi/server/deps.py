"""Lazy shared dependencies and HTTP API-key authentication."""

import hmac
import os
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException

from gs_openapi.core.client import GausiumAPIClient
from gs_openapi.v3.api import GausiumV3


@lru_cache
def get_v3() -> GausiumV3:
    return GausiumV3(GausiumAPIClient())


@lru_cache
def get_sessions():
    from gs_openapi.agent.session import InMemorySessionStore

    return InMemorySessionStore()


@lru_cache
def get_confirms():
    from .routes.agent import PendingConfirms

    return PendingConfirms()


@lru_cache
def get_agent():
    from gs_openapi.agent.core import PiAgent
    from gs_openapi.agent.settings import AgentSettings, build_provider

    settings = AgentSettings()
    return PiAgent(
        get_v3(), build_provider(settings),
        auto_approve=settings.pi_agent_auto_approve,
        max_turns=settings.pi_agent_max_turns,
        confirm_gate=get_confirms(),
    )


V3Dep = Annotated[GausiumV3, Depends(get_v3)]
SessionsDep = Annotated[Any, Depends(get_sessions)]
AgentDep = Annotated[Any, Depends(get_agent)]
ConfirmsDep = Annotated[Any, Depends(get_confirms)]


async def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    expected = os.getenv("GS_SERVER_API_KEY")
    if expected and (x_api_key is None or not hmac.compare_digest(x_api_key, expected)):
        raise HTTPException(status_code=401, detail="Invalid API key")
