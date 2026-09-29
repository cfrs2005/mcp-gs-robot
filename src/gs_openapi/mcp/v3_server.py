"""MCP stdio server backed by the shared V3 tool registry."""

from __future__ import annotations

import inspect
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..core.client import GausiumAPIClient
from ..core.errors import GausiumAPIError
from ..tools.registry import REGISTRY, invoke
from ..v3.api import GausiumV3


def build_mcp(name: str = "gs-robot") -> FastMCP:
    mcp = FastMCP(name)
    v3: GausiumV3 | None = None

    for spec in REGISTRY.values():
        # FastMCP discovers field names/types/defaults from inspect.signature.
        # Bind the tool name as a closure (not an MCP parameter).
        async def call(*, _tool_name: str = spec.name, **kwargs: Any) -> Any:
            nonlocal v3
            if v3 is None and _tool_name != "describe_work_state":
                v3 = GausiumV3(GausiumAPIClient())
            try:
                return await invoke(_tool_name, kwargs, v3)
            except GausiumAPIError as exc:
                return {"error": {"code": exc.code, "message": exc.msg,
                                  "trace_id": exc.trace_id}}

        call.__name__ = spec.name
        call.__doc__ = spec.description
        call.__signature__ = inspect.Signature([
            inspect.Parameter(field_name, inspect.Parameter.KEYWORD_ONLY,
                              annotation=field.annotation,
                              default=field.default if not field.is_required() else inspect.Parameter.empty)
            for field_name, field in spec.input_model.model_fields.items()
        ], return_annotation=Any)
        mcp.add_tool(call, name=spec.name, description=spec.description)
    return mcp
