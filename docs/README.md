# V3 documentation

The [architecture contract](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md) is the source of truth for entry points, tool names, input shapes, and environment settings. The runtime [tool registry](https://github.com/cfrs2005/mcp-gs-robot/blob/main/src/gs_openapi/tools/registry.py) supplies MCP, Pi Agent, and REST tool calls. Robot listing remains on v1alpha1 because V3 has no list endpoint.

| Guide | Purpose |
|---|---|
| [English README](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md) / [中文 README](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README_CN.md) | Install, run, and browse all 40 tools |
| [API index](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) | 38 archived OpenAPI V3 endpoints with official links; legacy notes |
| [Testing guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) | Unit tests, mock backend, REST/SSE, MCP inspector |
| [Claude Code integration](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md) | MCP stdio and Skill setup |
| [Skill guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md) | Install the reusable skill |
| [OpenAPI V3 archive](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/openapi-v3/overview.md) | Archived public documentation, including references and endpoint pages |

The HTTP server exposes FastAPI Swagger at `http://localhost:8000/docs`. The H5 build in `h5/` is packaged into `src/gs_openapi/server/static/`; the MCP server uses stdio, not SSE. Never use real credentials in tests or commit them.
