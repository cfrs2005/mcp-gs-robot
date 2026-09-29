"""Public service health endpoint."""

from fastapi import APIRouter

from gs_openapi import __version__
from gs_openapi.tools.registry import REGISTRY

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    from gs_openapi.agent.settings import AgentSettings

    return {
        "status": "ok", "version": __version__,
        "agent_provider": AgentSettings().pi_agent_provider, "tools": len(REGISTRY),
    }
