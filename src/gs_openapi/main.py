"""MCP stdio entrypoint; V3 tools are registered by default."""

import logging
import os
import sys

from dotenv import load_dotenv

from .mcp.v3_server import build_mcp

LOG_FORMAT = "%(asctime)s.%(msecs)03d - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Building tool schemas performs no network calls or credential checks.
mcp = build_mcp()


def main():
    """Start the V3 MCP server over stdio, optionally exposing prefixed legacy tools."""
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT,
                        stream=sys.stderr)
    if os.getenv("GS_ENABLE_LEGACY_TOOLS") == "1":
        from .mcp.gausium_mcp import GausiumMCP
        from .mcp.legacy_tools import register_legacy_tools
        from .utils.robot_router import RobotAPIRouter

        legacy = GausiumMCP("gs-openapi-legacy")
        register_legacy_tools(mcp, legacy, RobotAPIRouter(legacy))
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
