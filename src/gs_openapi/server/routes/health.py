"""Public health endpoint plus a protected, side-effect-free auth probe."""

import os

from fastapi import APIRouter

from gs_openapi import __version__
from gs_openapi.tools.registry import REGISTRY

router = APIRouter()
protected_router = APIRouter()


@router.get("/health")
async def health() -> dict:
    from gs_openapi.agent.settings import AgentSettings

    return {
        "status": "ok", "version": __version__,
        "agent_provider": AgentSettings().saodi_provider, "tools": len(REGISTRY),
        # Only whether a key is configured -- never the key itself.
        "auth_required": bool(os.getenv("GS_SERVER_API_KEY")),
    }


@protected_router.get("/auth/check")
async def auth_check() -> dict:
    """Mounted under the API-key guard: 200 means the supplied key is accepted."""
    return {"ok": True}
