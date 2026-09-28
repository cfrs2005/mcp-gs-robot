"""Generic registry-backed tool endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from gs_openapi.tools import registry

from .. import deps

router = APIRouter()


@router.post("/tools/{tool_name}")
async def call_tool(
    tool_name: str, body: dict[str, Any], v3: deps.V3Dep,
) -> dict:
    if tool_name not in registry.REGISTRY:
        raise HTTPException(status_code=404, detail="Unknown tool")
    return {"result": await registry.invoke(tool_name, body, v3)}
