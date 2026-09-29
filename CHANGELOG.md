# Changelog

All notable changes to this project are documented here.

## [0.4.1] - 2026-09-29

### 🔧 Changed
- README showcase images (`docs/images/h5-showcase.png`, `h5-showcase_cn.png`) now show the 0.4.0 interface: home, result cards, execution pipeline, robots and current location; the H5 feature description in `README.md` / `README_CN.md` is updated to match.
- Deprecation notices now state that `pi-agent`, `PiAgent` and `PI_AGENT_*` are removed in 0.5.0.

## [0.4.0] - 2026-09-29

### 🚀 Added
- **H5 brand and design tokens**: new Saodi AI logo (`docs/images/logo*.svg`) and robot-head mark (favicon, header, avatar); one token file (`h5/src/shared/tokens.css`) for colors, radii, shadows, type and spacing, also overriding Vant's theme variables.
- **Chat result cards**: a single tool → card table (`components/cards/registry.ts`) renders `get_robot_status`, `list_task_reports` (KPI tiles, per-day area chart in hand-written SVG, recent reports) and map images for both live streams and replayed history; the raw JSON stays expandable. Rule-based follow-up chips, suggested questions on the empty chat, a retry button and message times for live messages.
- **Dangerous-tool pipeline card**: confirm → sent → delivery, driven by the confirmation, the tool result and a later `get_command_status` / `wait_for_command` for the same `requestId` (`cmdStatus` 6 is shown as "delivered", not "done").
- **Mermaid diagrams** in chat: ```` ```mermaid ```` fences render as diagrams (`securityLevel: 'strict'`, design-token theme, SVG re-sanitized with DOMPurify). `mermaid` 12 is lazily imported into its own chunks only when a closed fence appears, so the first-screen bundle is unaffected; parse errors fall back to the source; wide diagrams scroll inside their card.
- **Robot list**: search by SN / name / map, filter chips (all / online / offline / unreachable / by work state / charging) and product photos by `modelTypeCode` (loaded at runtime, never bundled; a drawn robot is the fallback).
- **Robot detail**: gradient hero with battery / map / work-state tiles, readable capability tags with the raw JSON collapsible, report KPIs, and a **current location card** that marks the robot (pulse + heading arrow) and map points / chargers on the map PNG (grid origin bottom-left, angle in degrees; read-only).
- Session JSON gains `confirmations` (`confirm_id`, `tool_use_id`, `name`, `input`, `summary`, `decision`, `at`, `after_message`); SSE `confirm_required` gains `tool_use_id`. History replay rebuilds the same pipeline card; rejected calls show "Rejected", not failed.

### 🔧 Changed
- **Structure-aware tool-result truncation** (`fit_tool_output`, budget `TOOL_RESULT_BUDGET = 20000` characters): an oversized result drops items from the tail of its largest list and notes `"_truncated": {"field", "kept", "total", "unit"}` on the holding object, falling back to a character prefix wrapped as `{"_truncated": …, "text": …}`. The result is always valid JSON, and the SSE `tool_result.output`, the stored `tool_result.content` (encoded once) and what the model sees come from the same cut. Cards say "M records in total, showing the first N".
- **Local store schema v2**: `sessions.confirmations` is added automatically and idempotently when a v1 database is opened; old rows read as an empty list.
- One fleet source (`h5/src/api/fleet.ts`) for online / offline / unreachable: the chat home overview and the robot list always show the same counts.
- Brand text is "Saodi AI" in both languages.

### 🐛 Fixed
- Tool results over 20k characters were cut mid-JSON (invalid for the model and the UI) and stored doubly encoded.
- `confirm_required` was not persisted, so replayed chats lost their confirmation cards and showed rejected calls as failures.

### ⚠️ Deprecated
- `pi-agent`, `PiAgent` and `PI_AGENT_*` (deprecated in 0.3.0) are still kept in this release; their removal is postponed to 0.5.0.

### Known limitations
- A confirmation that times out (120 s) is recorded as `rejected`: the confirm gate only reports approved / not approved.
- Replay of an approved pipeline (sent → delivered) is covered by tests only; it was not exercised against a real robot.
- Sessions saved by 0.3.0 keep their truncated tool results as raw text (no result card).

## [0.3.0] - 2026-09-29

### 🚀 Added
- **Saodi cognition layers**: each session's system prompt is Soul (`agent/soul.md`) → Knowledge (the `skills/gs-robot` skill: `references/domain.md`, `SKILL.md`, `references/work-states.md`) → Memory (`references/experience.md`) → **local memory** (`$SAODI_DATA_DIR/memory.md`) → optional private `$SAODI_CONTEXT_DIR/*.md`, capped by `SAODI_CONTEXT_MAX_CHARS` (default 60000; oldest local memory entries are dropped first). `saodi --show-context` prints the final prompt without an LLM key. The wheel ships the skill as `gs_openapi/_skills/gs-robot`.
- **`remember` tool** (dangerous, confirmation required): appends one verified lesson to the local memory file as `- [YYYY-MM-DD] lesson`, de-duplicates normalised text and refuses credential-looking content (token/secret key=value, Bearer, `sk-…`, JWTs, long random strings).
- **`lookup_error_code` tool** (read-only, local): returns matching rows from `references/error-codes.md` (with table headers) and entries from `references/experience.md`; a "do not guess" hint when nothing matches.
- `ToolSpec.local` marks tools that need no upstream client (`describe_work_state`, `lookup_error_code`, `remember`).
- **SQLite persistence** (`gs_openapi.store`, `$SAODI_DATA_DIR/saodi.sqlite`): agent sessions survive restarts; `GET /api/v1/agent/sessions` lists history; dangling `tool_use` from an interrupted stream is closed before the next turn.
- **Tool-call log and error threads**: every `registry.invoke` (agent / REST / MCP) is recorded with redacted args; failures are folded by fingerprint into threads with auto-classification (110003 → account_permission, 230003 → robot_offline, response-model mismatches → our_bug) and regression reopening. `GET/PATCH /api/v1/errors/threads…`.
- **CLI**: `saodi errors [list|show <id>|promote <id>]` and `saodi memory [show|add "<lesson>"|edit]`.
- `GET /api/v1/health` returns `auth_required`; new `GET /api/v1/auth/check` validates the API key without calling upstream.
- **H5**: Markdown rendering (marked + DOMPurify), sandboxed HTML preview, an ordered tool-call timeline, a history drawer, English / 中文 switch (follows the browser on first visit), and a 401 prompt that leads to Settings.
- Docs: 5-minute quick start, a copy-paste [agent setup prompt](docs/AGENT_SETUP_PROMPT.md), cognition & memory guide, troubleshooting table.

### 🔧 Changed
- The agent is renamed to **Saodi (扫地僧)**: command `saodi`, class `SaodiAgent`, variables `SAODI_PROVIDER` / `SAODI_MODEL` / `SAODI_AUTO_APPROVE` / `SAODI_MAX_TURNS`.
- Soul, `domain.md`, `experience.md` and `SKILL.md` are now written in English; Saodi **replies in the user's language** (key field names stay in English). Terminal prompts are in English.
- The ~23 KB error-code table is no longer resident in the system prompt (looked up on demand): `saodi --show-context` shrinks from 51,685 to 32,028 bytes.
- `.env` is loaded from the current working directory by every entry point (`gs_openapi.config.load_env`), so a wheel install finds it too and `GS_SERVER_HOST` / `GS_SERVER_PORT` from `.env` apply.
- Tool-call args are additionally scrubbed for `key=value` secrets typed into free-text fields.
- Robot list degrades gracefully when some robots are offline: a batch that fails with 230003 is re-queried per robot (0.1 s apart, respecting the 100026 rate limit); the H5 renders online / offline / unreachable states and an offline banner on the detail page.

### 🐛 Fixed
- `TaskReport`: percentage fields are floats upstream (`completionPercentage`, battery and consumables percentages), which caused HTTP 422; five missing int fields were added.
- `RobotMap`: all fields optional; `map_id` falls back to `robotMapUuid` when the upstream omits `mapId`.
- H5 chat: streaming render, dangerous-operation confirmation no longer hangs; robot list fills `robotSn`; session creation body is optional.

### ⚠️ Deprecated
- `pi-agent` command, `PiAgent` class alias and `PI_AGENT_*` variables still work for one release and emit a deprecation warning; they will be removed in the next release.

## [0.2.0] - 2026-09-28

### 🚀 Added
- OpenAPI V3 client covering 36 robot/task endpoint tools plus OAuth token operations, with typed models and reference tables (38 archived endpoint pages).
- Shared 40-tool registry: 36 V3 endpoint tools, legacy robot listing, local work-state lookup, and two workflow tools; MCP, the agent, and REST share the definitions.
- Agent CLI and HTTP chat with Anthropic and OpenAI-compatible providers, streaming SSE and confirmation gates.
- FastAPI REST server, robot routes, API-key option, and Vue/Vite H5 interface.
- Cross-client gs-robot Skill, V3 endpoint index (`docs/apis.md`) linking to the official documentation, automated tests, CI, and container packaging.

### 🔧 Changed
- V3 tools are the MCP default; package now exposes `mcp-gs-robot`, `gs-robot-server`, and the agent CLI.
- Tool inputs use snake_case; agent dangerous operations require explicit confirmation by default.

### 🐛 Fixed
- OAuth token handling uses the returned `expires_in` lifetime correctly.
- Updated V3 endpoint mapping and documentation to match the official public reference.

### ⚠️ Breaking
- Old 0.1.x MCP tool names and smart-routing tools are no longer registered by default. Set `GS_ENABLE_LEGACY_TOOLS=1` to expose them under `legacy_`-prefixed names; migrate clients to the [V3 tool list](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md).

## [0.1.12] - 2025-09-02

### 🎯 Smart Routing Enhancement
- Enhanced smart routing strategy to use serial number prefix detection
- Improved robot series identification performance by eliminating API dependency
- Updated automatic routing detection to handle additional robot series prefixes
- Optimized intelligent routing for better reliability and faster response times

### 🔧 Technical Improvements
- Streamlined robot series detection logic in RobotAPIRouter
- Enhanced prefix-based routing mapping for comprehensive robot coverage
- Improved error handling and fallback strategies for unknown robot types
- Added comprehensive test coverage for prefix-based routing functionality

## [0.1.11] - 2025-08-30

### 🧹 Major Interface Cleanup
- Removed redundant MCP tools to eliminate confusion for AI models
- Consolidated robot status tools: removed get_robot_status, get_robot_status_v1, get_robot_status_v2
- Consolidated batch status tools: removed batch_get_robot_statuses_v1, batch_get_robot_statuses_v2
- Consolidated task reports: removed list_robot_task_reports, list_robot_task_reports_s
- Added batch_get_robot_statuses_smart for intelligent batch status queries

### 🎯 Simplified Tool Set
- Reduced from 21 tools to 16 tools (23% reduction)
- All remaining tools use smart routing (automatic M-line/S-line detection)
- Users only need to use `_smart` versions - no need to know robot series details

## [0.1.10] - 2025-08-30

### 🔧 Map Subareas API Fix
- Fixed map subareas API path from `/map/{map_id}/subareas` to `/map/subareas/get`
- Corrected method from GET to POST according to official documentation
- Updated API version from V2alpha1 to V1 (matches official curl examples)
- Fixed request format to use JSON body with mapId and robotSn parameters

## [0.1.9] - 2025-08-30

### 🔧 Critical API Path Fixes
- Fixed V2 S-line robot status API paths to include required `/s/` prefix
- Corrected map API version from V2alpha1 back to V1 (per official documentation)
- Fixed README navigation links to use GitHub absolute URLs for PyPI compatibility
- Updated API version constant name (OPENAPI_V2ALPHA1 → OPENAPI_V2_ALPHA1)

### 📚 Documentation
- Enhanced navigation links for better PyPI page experience
- Verified all API endpoints against official Gausium documentation

## [0.1.8] - 2025-08-30

### 🔧 API Fixes
- Fixed map API endpoints from V1 to V2alpha1 version for proper compatibility
- Corrected map API method from GET to POST according to API specification
- Fixed API version constant name (OPENAPI_V2ALPHA1 → OPENAPI_V2_ALPHA1)
- Updated robot list API to use relation=bound parameter for better filtering

### 🚀 New Features
- Added intelligent robot routing system for automatic API version selection
- Implemented RobotAPIRouter class to distinguish M-line vs S-line robots
- Added smart routing MCP tools: get_robot_status_smart, get_task_reports_smart, get_robot_capabilities
- Enhanced robot series detection (M-line: 40/50/75/OMNIE, S-line: S/SW)

### 🧹 Cleanup
- Updated .gitignore to exclude documentation templates and development files
- Improved project file organization

## [0.1.7] - 2025-08-30

### 🎨 Visual Improvements
- Completely redesigned architecture diagram with improved layout and clarity
- Fixed background layer alignment and proper component masking
- Moved architecture diagram components 50px to the right for better spacing
- Aligned all layer labels for consistent visual presentation
- Removed all connection lines for cleaner, simplified diagram appearance
- Enhanced layer visibility with proper background colors and opacity

## [0.1.6] - 2025-08-30

### 📝 Documentation
- Enhanced README with comprehensive badges, icons, and professional layout
- Added detailed Claude Code integration with environment variable configuration
- Fixed PyPI image display using absolute GitHub raw URLs
- Added bilingual support (English/Chinese) with collapsible sections
- Created dedicated Claude Code integration guide
- Added comprehensive IDE support matrix

### 🔧 Improvements
- Corrected stdio transport mode documentation (removed incorrect SSE references)
- Added three methods for Claude Code MCP configuration
- Enhanced installation instructions with multiple options

## [0.1.5] - 2025-08-29

### 🐛 Fixed
- Fixed package import path issues for proper MCP server execution
- Corrected executable entry point configuration in pyproject.toml
- Fixed PyPI publishing GitHub Secret naming convention

## [0.1.4] - 2025-08-29

### 🚀 Features
- Renamed package to `mcp-gs-robot` for PyPI distribution
- Configured PyPI publishing with stdio transport mode

## [0.1.3] - 2025-08-29

### 🚀 Features
- Complete Gausium OpenAPI MCP server implementation
- Added architecture diagrams and updated README with uv instructions

## [0.1.2] - 2025-08-29

### 🎨 Documentation
- Implemented Gausium OpenAPI MCP server structure and tools

## [0.1.1] - 2025-08-29

### 📝 Documentation
- Updated installation instructions using GitHub installation method

## [0.1.0] - 2025-04-30

### 🎉 Initial Release
- Initial commit: basic Gausium robot MCP plugin
