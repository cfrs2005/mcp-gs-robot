"""MCP schema and entrypoint integration checks."""

import importlib

from gs_openapi.core.errors import GausiumAPIError
from gs_openapi.mcp.v3_server import build_mcp
from gs_openapi.tools.registry import REGISTRY


async def test_mcp_lists_all_registry_tools_with_field_schemas():
    server = build_mcp()
    tools = await server.list_tools()
    assert len(tools) == len(REGISTRY)
    by_name = {item.name: item for item in tools}
    assert set(by_name) == set(REGISTRY)
    assert "robot_sn_list" in by_name["get_robot_status"].inputSchema["required"]
    assert "map_id" in by_name["navigate_home"].inputSchema["required"]
    assert "page_size" in by_name["list_robots"].inputSchema["properties"]
    result = await server.call_tool("describe_work_state", {"work_state": 100})
    assert '"name": "IDLE"' in result[0].text


async def test_mcp_returns_structured_upstream_error(monkeypatch):
    from gs_openapi.mcp import v3_server

    class FailingClient:
        async def call_endpoint(self, *args, **kwargs):
            raise GausiumAPIError("offline", code=123, trace_id="trace")

    monkeypatch.setattr(v3_server, "GausiumAPIClient", FailingClient)
    result = await build_mcp().call_tool("list_robots", {})
    assert '"code": 123' in result[0].text
    assert '"trace_id": "trace"' in result[0].text


def test_main_import_has_no_runtime_side_effects(monkeypatch):
    from mcp.server.fastmcp import FastMCP

    def fail(*args, **kwargs):
        raise AssertionError("import must not start MCP transport")

    monkeypatch.setattr(FastMCP, "run", fail)
    main = importlib.import_module("gs_openapi.main")
    importlib.reload(main)
    assert main.mcp is not None
