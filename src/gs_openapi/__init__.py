"""Gausium OpenAPI V3 toolkit: MCP server, HTTP server, Saodi (扫地僧) agent."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mcp-gs-robot")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    __version__ = "0.0.0"

__all__ = ["__version__"]
