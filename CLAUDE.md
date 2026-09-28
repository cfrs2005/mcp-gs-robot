# mcp-gs-robot · AI coding guide

> Unofficial open-source software for personal research; not affiliated with, endorsed by, or supported by Gausium. Use at your own risk.

## Layout

- `docs/ARCHITECTURE_V3.md`: authoritative V3 contract for names, input shapes, entry points, and environment variables. Update it before changing the contract.
- `src/gs_openapi/v3/`: typed V3 OpenAPI client and reference tables.
- `src/gs_openapi/tools/registry.py`: single source of truth for all MCP, Agent, and REST tools; `v3_tools.py` and `workflow_tools.py` register handlers.
- `src/gs_openapi/mcp/` and `src/gs_openapi/main.py`: stdio MCP server and optional legacy tools.
- `src/gs_openapi/agent/`: Pi Agent, providers, sessions and CLI.
- `src/gs_openapi/server/`: FastAPI REST/SSE app and H5 static assets.
- `h5/`: Vue/Vite H5 frontend, builds into `src/gs_openapi/server/static/`.
- `skills/gs-robot/`: reusable Agent Skill; `docs/openapi-v3/`: archived public reference.
- `tests/`: offline unit/integration tests with mock HTTP transport.

## Commands

```sh
uv sync --extra dev
uv run pytest -q
uv run ruff check src tests
cd h5 && npm ci && npm run build
uv run gs-robot-server
uv run mcp-gs-robot
```

Run H5 commands from `h5/`; run Python commands from the repository root. Start `gs-robot-server` for `/api/v1` and H5 `/`, or `mcp-gs-robot` for MCP stdio. `pi-agent` opens the terminal REPL. Build H5 before `uv build` to include it in the wheel.

## Conventions

- The registry is the sole source of tools; never define a separate MCP/Agent/REST tool list.
- Use snake_case for input models, mapping to upstream camelCase only at the V3 boundary.
- Never log secrets or commit credentials; use `.env.example` placeholders. Robot commands can move physical machines; test on simulators/idle robots first.
- Mark mutating/motion tools `dangerous=True` and require confirmation in Agent/Skill; direct REST clients must confirm before invoking.

## Adding a V3 tool

1. Check the relevant archived page in `docs/openapi-v3/` and update the contract first.
2. Add/extend V3 request/response models and a `GausiumV3` method as needed.
3. Add a snake_case input model and registered handler in `src/gs_openapi/tools/v3_tools.py`; set its category, bilingual description, and `dangerous` flag.
4. Add mock-backed tests for validation, payload mapping and invocation; update docs and Skill references.
5. Run pytest, ruff, H5 build and verify the wheel contains static assets.
