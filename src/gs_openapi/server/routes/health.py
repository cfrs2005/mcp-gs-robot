"""Public service health endpoint."""

from fastapi import APIRouter

from gs_openapi.tools.registry import REGISTRY

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    from gs_openapi.agent.settings import AgentSettings

    return {
        "status": "ok", "version": "0.2.0",
        "agent_provider": AgentSettings().pi_agent_provider, "tools": len(REGISTRY),
    }
