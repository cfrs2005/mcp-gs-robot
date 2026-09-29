# mcp-gs-robot · AI coding guide

> Unofficial open-source software for personal research; not affiliated with, endorsed by, or supported by Gausium. Use at your own risk.

## Layout

- `docs/ARCHITECTURE_V3.md`: authoritative V3 contract for names, input shapes, entry points, and environment variables. Update it before changing the contract.
- `src/gs_openapi/v3/`: typed V3 OpenAPI client and reference tables.
- `src/gs_openapi/tools/registry.py`: single source of truth for all MCP, Agent, and REST tools; `v3_tools.py`, `workflow_tools.py` and `knowledge_tools.py` (`lookup_error_code`, `remember`) register handlers. `ToolSpec.local=True` marks tools that need no upstream client.
- `src/gs_openapi/mcp/` and `src/gs_openapi/main.py`: stdio MCP server and optional legacy tools.
- `src/gs_openapi/agent/`: Saodi (扫地僧) agent, providers, sessions and CLI. `soul.md` (English; reply in the user's language) is the identity/safety layer; `prompts.py` builds the system prompt Soul → Knowledge → Memory (experience.md, then local `memory.md`) → `$SAODI_CONTEXT_DIR/*.md`. `error-codes.md` is not resident; the agent calls `lookup_error_code`.
- `src/gs_openapi/server/`: FastAPI REST/SSE app and H5 static assets.
- `src/gs_openapi/store/`: stdlib `sqlite3` persistence at `$SAODI_DATA_DIR/saodi.sqlite` (default `~/.saodi/`; `db.py` `MIGRATIONS` adds later columns idempotently): agent sessions (messages, errors and `confirmations` for replaying confirm cards), the tool-call log (recorded once in `registry.invoke` via a call observer) and error threads; `saodi errors` reads it. `memory.py` owns the private local memory `$SAODI_DATA_DIR/memory.md` (one `- [YYYY-MM-DD] lesson` per line, de-duplicated, credential-looking text refused).
- `h5/`: Vue/Vite H5 frontend, builds into `src/gs_openapi/server/static/`.
  - `h5/src/shared/tokens.css`: design tokens (color, radius, shadow, type, spacing) and the Vant `--van-*` overrides; components use only these variables. `shared/mark.svg` is the Saodi AI robot-head mark (favicon, header, avatar); `shared/robotModels.ts` maps `modelTypeCode` (exact, then displayName/code keywords) to remote product images, never bundled; `shared/reports.ts` / `format.ts` hold report KPIs, per-day area and number/time formatting.
  - `h5/src/shared/markdown.ts`: `renderSegments` splits model text into DOMPurify-sanitized markdown runs and special fences (`html` → sandboxed `HtmlPreview`, `mermaid` → `components/ui/MermaidView.vue`), each with `closed` so unfinished fences show source while streaming. `mermaid` is the only diagram dependency and is loaded by dynamic import (separate chunks, never in the first-screen bundle); its SVG is re-sanitized (svg profile) and parse errors fall back to the source.
  - `h5/src/components/cards/registry.ts`: the single tool name → result card table (robot status, task reports, map images) used by `ToolGroup` for both live SSE and replayed history; results cut by the server carry `_truncated` (see `fit_tool_output` in `agent/core.py`, ARCHITECTURE_V3 §4) and the card says how many rows it shows. `components/ui/` holds the shared pieces (robot image, battery, status pill, KPI tiles, hand-drawn SVG bar chart, map thumbnail, card shell); `components/chat/` holds the chat header, composer, welcome home, dangerous-tool pipeline card, rule-based follow-ups and `timeline.ts` (event/transcript → reply parts).
  - `h5/src/components/cards/LocateCard.vue`: robot detail "Current location": the current map PNG with the robot (pulse + heading arrow) and map points / chargers overlaid in percent coordinates (left = x / gridWidth, top = (gridHeight - y) / gridHeight; angle in degrees, 0 = +x, CCW; canvas mapInfo wins). Read-only data: status, map canvas, map resources, and `list_charging_positions` through the generic `POST /api/v1/tools/{name}` (`callTool` in `api/client.ts` accepts read-only names only).
  - `h5/src/api/fleet.ts`: the fleet in one place: 60 s caches of `list_robots` (model lookup by SN) and of `list_robots` + live batch status (`loadFleetStatus`); `fleetState()` is the only online / offline / unreachable definition and `fleetSummary()` the only counter, used by both the chat home overview and the robot list. `api/settings.ts` is the API base/key store.
- `skills/gs-robot/`: reusable Agent Skill and the single source of Saodi's Knowledge/Memory (packed into the wheel as `gs_openapi/_skills/gs-robot` via hatch force-include); `references/experience.md` is open-source call experience — never write SNs, traceIds, accounts, secrets or customer/site names there; `docs/apis.md`: V3 endpoint index with links to the official documentation.
- `docs/AGENT_SETUP_PROMPT.md`: copy-paste setup prompt for coding agents (English + Chinese; also embedded in the READMEs).
- `README.md` (English, primary) / `README_CN.md` (Chinese mirror): keep their sections aligned.
- `tests/`: offline unit/integration tests with mock HTTP transport.

## Commands

```sh
uv sync --extra dev
uv run pytest -q
uv run ruff check src tests
cd h5 && npm ci && npm run build
uv run gs-robot-server
uv run mcp-gs-robot
uv run saodi --show-context          # print the system prompt (no LLM key)
uv run saodi memory [add "<lesson>" | edit]
uv run saodi errors [show <id> | promote <id>]
```

Run H5 commands from `h5/`; run Python commands from the repository root. Start `gs-robot-server` for `/api/v1` and H5 `/`, or `mcp-gs-robot` for MCP stdio. `saodi` opens the terminal REPL (`saodi --show-context` prints the system prompt; `pi-agent` / `PI_AGENT_*` are deprecated aliases kept for one release). Build H5 before `uv build` to include it in the wheel. Every entry point loads `.env` from the current working directory (`gs_openapi.config.load_env`).

## Conventions

- The registry is the sole source of tools; never define a separate MCP/Agent/REST tool list.
- Use snake_case for input models, mapping to upstream camelCase only at the V3 boundary.
- Never log secrets or commit credentials; use `.env.example` placeholders. Robot commands can move physical machines; test on simulators/idle robots first.
- Mark mutating/motion tools `dangerous=True` and require confirmation in Agent/Skill; direct REST clients must confirm before invoking.

## Adding a V3 tool

1. Read the endpoint's page in the official Gausium OpenAPI V3 documentation (links in `docs/apis.md`) and update the contract first.
2. Add/extend V3 request/response models and a `GausiumV3` method as needed.
3. Add a snake_case input model and registered handler in `src/gs_openapi/tools/v3_tools.py`; set its category, bilingual description, and `dangerous` flag.
4. Add mock-backed tests for validation, payload mapping and invocation; update docs and Skill references.
5. Run pytest, ruff, H5 build and verify the wheel contains static assets.
