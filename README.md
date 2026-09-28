# 🤖 mcp-gs-robot

<div align="center">

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-gs-robot.svg)](https://pypi.org/project/mcp-gs-robot/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)
[![CI](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![OpenAPI V3](https://img.shields.io/badge/Gausium_OpenAPI-V3-orange.svg)](https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Overview)

**Talk to your Gausium cleaning robots — from Claude, Cursor, a terminal, or your phone.**

*MCP server · HTTP/REST server · Pi Agent (CLI + H5) · Agent Skill — one codebase, one tool registry, Gausium OpenAPI V3.*

[Quick Start](#-quick-start) · [MCP Tools](#-mcp-tools) · [Pi Agent](#-pi-agent) · [HTTP API & H5](#-http-api--h5) · [Configuration](#-configuration) · [Development](#-development) · [中文文档](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README_CN.md)

</div>

> ⚠️ **Disclaimer** — This is an **unofficial, open-source project for personal research and learning**. It is not affiliated with, endorsed by, or supported by Gausium (高仙). Use at your own risk. Robot commands move physical machines: test on simulators or idle robots first. Built solely from the public [Gausium OpenAPI V3 documentation](https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Overview).

---

## 🌟 What is this?

`mcp-gs-robot` wraps the Gausium OpenAPI **V3** (robot status, maps, combined tasks, schedules, commands, reports) into a typed Python client, and exposes it through four entry points that share **one tool registry**:

| Entry point | Command | Use it when… |
|---|---|---|
| 🔌 **MCP Server** (stdio) | `mcp-gs-robot` | You want Claude Code, Claude Desktop, Cursor, Cherry Studio or any MCP client to operate robots |
| 🌐 **HTTP Server** (FastAPI) | `gs-robot-server` | You want REST endpoints, Swagger, and the built-in **H5 mobile web app** |
| 🧠 **Pi Agent** (CLI + H5 chat) | `pi-agent` | You want a chat assistant that plans and executes robot operations with confirmation gates |
| 📚 **Agent Skill** | `skills/gs-robot/` | You want to teach Claude Code / Codex / WorkBuddy the correct operating procedure |

### ✨ Highlights

- **40 tools** covering all 36 V3 business endpoints plus workflow helpers (`run_cleaning_task`, `wait_for_command`)
- **Typed & tested** — pydantic v2 models, envelope unwrapping, six-digit error codes surfaced as `GausiumAPIError`, 48 unit tests, no network needed
- **Safety first** — every mutating/moving tool is flagged `dangerous` and requires explicit confirmation in the Agent, CLI and H5
- **Correct OAuth handling** — V3 returns `expires_in` as a millisecond epoch; the token manager handles it (and refreshes under a lock)
- **Built strictly on the official docs** — every endpoint follows the [Gausium OpenAPI V3 documentation](https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Overview); [`docs/apis.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) maps each one to its official page
- **Provider-agnostic Agent** — Anthropic (default, `claude-opus-5`) or any OpenAI-compatible endpoint (DeepSeek, local models…)

## 🏗️ Architecture

![Architecture](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/architecture.svg)

```
 Claude / Cursor / MCP clients      Browser (H5)        Terminal
            │                          │                   │
   ┌────────▼────────┐        ┌────────▼────────┐  ┌───────▼───────┐
   │  MCP Server     │        │  HTTP Server    │  │  pi-agent CLI │
   │  gs_openapi.mcp │        │  REST + SSE     │  │               │
   └────────┬────────┘        └───┬─────────┬───┘  └───────┬───────┘
            │                     │         │              │
            │                     │   ┌─────▼──────────────▼─────┐
            │                     │   │  Pi Agent (tool loop,     │
            │                     │   │  confirm gate, providers) │
            │                     │   └─────────────┬─────────────┘
   ┌────────▼─────────────────────▼─────────────────▼─────────────┐
   │              Tool Registry  (gs_openapi.tools)  — 40 tools    │
   └──────────────────────────────┬────────────────────────────────┘
   ┌──────────────────────────────▼────────────────────────────────┐
   │   GausiumV3 client · models · references · token manager      │
   └──────────────────────────────┬────────────────────────────────┘
                                  ▼
                    https://openapi.gs-robot.com  (OpenAPI V3)
```

The full contract (tool names, REST/SSE protocol, agent interface) lives in [`docs/ARCHITECTURE_V3.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md).

## 🚀 Quick Start

### 1. Install

```bash
pip install mcp-gs-robot          # or: uv pip install mcp-gs-robot
```

From source:

```bash
git clone https://github.com/cfrs2005/mcp-gs-robot.git
cd mcp-gs-robot
uv sync                            # creates .venv with all runtime deps
```

### 2. Credentials

Create an application and an AccessKey in the [Gausium Developer Center](https://developer.gs-robot.com/), then:

```bash
export GS_CLIENT_ID="cli-xxxxxxxx"
export GS_CLIENT_SECRET="sk-xxxxxxxx"
export GS_OPEN_ACCESS_KEY="ak-xxxxxxxx"     # the AccessKeySecret, not the AccessKeyID
```

A `.env` file in the working directory is also loaded. See [`.env.example`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/.env.example). Never commit credentials.

### 3. Pick an entry point

<details open>
<summary><b>🔌 MCP Server — Claude Code / Claude Desktop / Cursor</b></summary>

```bash
# Claude Code (one line)
claude mcp add gs-robot \
  --env GS_CLIENT_ID="…" --env GS_CLIENT_SECRET="…" --env GS_OPEN_ACCESS_KEY="…" \
  -- mcp-gs-robot
```

Or in `claude_desktop_config.json` / Cursor MCP settings:

```json
{
  "mcpServers": {
    "gs-robot": {
      "command": "mcp-gs-robot",
      "env": {
        "GS_CLIENT_ID": "…",
        "GS_CLIENT_SECRET": "…",
        "GS_OPEN_ACCESS_KEY": "…"
      }
    }
  }
}
```

Then just ask: *“List my robots and show battery and work state”* → `list_robots` + `get_robot_status`.
Transport is **stdio**. Set `GS_ENABLE_LEGACY_TOOLS=1` to also expose the 0.1.x tools as `legacy_*`.

</details>

<details>
<summary><b>🌐 HTTP Server + H5 mobile app</b></summary>

```bash
gs-robot-server                    # http://0.0.0.0:8000
```

- **H5 app**: open `http://localhost:8000/` on your phone or browser
- **Swagger**: `http://localhost:8000/docs`
- **Protect it**: set `GS_SERVER_API_KEY=…` and send `X-API-Key` (the H5 has a Settings page for it)

Docker:

```bash
cp .env.example .env && $EDITOR .env
docker compose up -d               # builds H5 + Python image, serves on :8000
```

</details>

<details>
<summary><b>🧠 Pi Agent — chat in the terminal</b></summary>

```bash
export ANTHROPIC_API_KEY="…"                 # default provider: Anthropic, model claude-opus-5
pi-agent --robot GS438-0120-X8P-0001

# or any OpenAI-compatible endpoint (DeepSeek, vLLM, Ollama…)
PI_AGENT_PROVIDER=openai OPENAI_BASE_URL=https://api.deepseek.com/v1 OPENAI_API_KEY=… \
PI_AGENT_MODEL=deepseek-chat pi-agent
```

```
› 一楼大厅的机器人现在什么状态？电量够不够跑一次清扫？
⚙ get_robot_status(robot_sn_list=["GS438-0120-X8P-0001"])
机器人在线，电量 82%，状态 IDLE（空闲），当前地图「一楼大厅」，可以执行任务。
› 用 sweep 模式清扫 area3
⚙ list_task_resources(...)  ⚙ create_task_definition(...)
⚠ 即将执行危险操作 start_task robot_sn=GS438-… fusion_task_id=… 确认？[y/N] y
⚙ start_task(...)  ⚙ wait_for_command(...)
命令已下发（cmdStatus=6），任务实例 47d029ee… 已开始。
```

</details>

<details>
<summary><b>📚 Agent Skill — Claude Code / Codex / WorkBuddy</b></summary>

```bash
# Claude Code (user scope)
cp -r skills/gs-robot ~/.claude/skills/gs-robot
# Codex CLI
cp -r skills/gs-robot ~/.codex/skills/gs-robot
```

The skill encodes the safe operating procedure (status → capabilities → resources → task definition → start → poll) and ships reference tables for work states, command types and task-start error codes. Details: [`skills/gs-robot/README.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md).

</details>

## 🧰 MCP Tools

All 40 tools are defined once in `gs_openapi/tools/` and exposed identically to MCP, the Agent and REST (`POST /api/v1/tools/{name}`). Inputs are `snake_case`; the registry maps them to the V3 `camelCase` fields. **⚠️ = dangerous** (moves a robot or mutates data; the Agent asks for confirmation).

<details open>
<summary><b>Robots & Maps</b></summary>

| Tool | Required inputs | Optional | Notes |
|---|---|---|---|
| `list_robots` | – | `page`, `page_size`, `relation` | Legacy `v1alpha1/robots` (V3 has no list endpoint) |
| `get_robot_status` | `robot_sn_list` (≤100) | | Adds `work_state_name` / `work_state_desc`; snapshots lag ≤30 s |
| `describe_work_state` | `work_state` | | Local lookup, no API call |
| `get_robot_capabilities` | `robot_sn` | | Combined-task / schedule support flags |
| `list_robot_maps` | `robot_sn` | | `mapId`, `mapVersionId`, `displayName` |
| `get_map_canvas` | `robot_sn`, `map_id` | | Temporary PNG URL + grid metadata |
| `list_charging_positions` | `robot_sn`, `map_id` | | |
| `list_map_resources` | `robot_sn`, `map_id_list` | `include_paths/regions/positions` | Resources without work modes |
| `list_task_resources` | `robot_sn`, `map_id_list` | `include_paths/regions/positions` | **Query this before creating tasks/schedules** |

</details>

<details>
<summary><b>Tasks (combined tasks)</b></summary>

| Tool | Required inputs | Optional | |
|---|---|---|---|
| `list_work_modes` | `robot_sn` | | |
| `list_task_definitions` | `robot_sn` | `page`, `pagesize`, `site_id`, `task_name` | |
| `get_task_definition` | `robot_sn`, `fusion_task_id` | | |
| `create_task_definition` | `robot_sn`, `task_name`, `work_mode`, `map_resource_list` | `loop_count`, `site_id`, `task_advance_config` | ⚠️ |
| `update_task_definition` | `robot_sn`, `fusion_task_id` | same as create | ⚠️ |
| `delete_task_definition` | `robot_sn`, `fusion_task_id` | | ⚠️ |
| `start_task` | `robot_sn`, `fusion_task_id` | `loop_count` | ⚠️ returns `requestId`, `taskInstanceId` |
| `pause_task` / `resume_task` / `stop_task` / `skip_task_item` | `robot_sn` | | ⚠️ |

</details>

<details>
<summary><b>Schedules</b></summary>

| Tool | Required inputs | |
|---|---|---|
| `create_simple_schedule` | `robot_sn`, `task_name`, `site_mode`, `work_mode`, `map_resource_list`, `plan_execute_type`, `plan_repeat_type`, `plan_start_date`, `plan_start_time` | ⚠️ |
| `update_simple_schedule` / `delete_simple_schedule` | `robot_sn`, `plan_uuid`, `year`, `month`, `day_of_month`, `operation_type` | ⚠️ |
| `create_schedule` / `update_schedule` / `delete_schedule` | standard schedule fields (see [docs](https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Overview)) | ⚠️ |
| `list_schedules` | `robot_sn` | |
| `get_schedule` | `robot_sn`, `plan_uuid`, `year`, `month`, `day_of_month` | |
| `get_schedule_calendar` | `robot_sn`, `year_month` | |
| `list_schedule_pre_tasks` | `robot_sn`, `date` | |

</details>

<details>
<summary><b>Commands, Reports & Workflows</b></summary>

| Tool | Required inputs | Optional | |
|---|---|---|---|
| `get_command_status` | `robot_sn`, `request_id` | | `cmdStatus=6` = delivered, **not** finished |
| `list_command_history` | `robot_sn` | `page`, `pagesize`, `cmd_status`, `command_type` | |
| `navigate_home` | `robot_sn`, `map_id` | `map_resource_id` | ⚠️ |
| `pause_navigation` / `resume_navigation` / `stop_navigation` | `robot_sn` | | ⚠️ |
| `list_task_reports` | `robot_sn` | `page`, `pagesize`, `end_time_min`, `end_time_max` | |
| `get_task_report_map_images` | `task_report_id` | `robot_sn` | |
| `wait_for_command` | `robot_sn`, `request_id` | `timeout_seconds` | Polls until a terminal `cmdStatus` |
| `run_cleaning_task` | `robot_sn`, `task_name`, `map_id`, `resource_ids` | `mode`, `strength`, `loop_count`, `wait_seconds` | ⚠️ capabilities → resources → create → start → poll |

</details>

Regenerate this list any time:

```bash
uv run python -c "from gs_openapi.tools.registry import REGISTRY; [print(t.category, t.name, '⚠️' if t.dangerous else '') for t in REGISTRY.values()]"
```

## 🧠 Pi Agent

The Pi Agent is a small, provider-neutral tool-use loop (`gs_openapi/agent/`) built on the same registry:

- **Providers**: `anthropic` (official SDK, streaming, adaptive thinking, prompt caching) or `openai` (any OpenAI-compatible `/chat/completions`)
- **Confirmation gate**: dangerous tools emit `confirm_required` and wait for approval — terminal `[y/N]` in the CLI, buttons in the H5, `POST …/confirm` over REST. `PI_AGENT_AUTO_APPROVE=1` disables this (not recommended)
- **Bounded**: `PI_AGENT_MAX_TURNS` (default 12) caps tool cycles; tool results are truncated at 20k chars
- **Same brain everywhere**: the CLI, the H5 chat and `POST /api/v1/agent/...` all run `PiAgent.run()`

## 🌐 HTTP API & H5

Base prefix `/api/v1`. `GET /api/v1/health` is public; everything else requires `X-API-Key` when `GS_SERVER_API_KEY` is set. Errors use one envelope: `{"error": {"code", "message", "trace_id"}}` (upstream V3 errors → HTTP 502 with the six-digit code).

| Area | Routes |
|---|---|
| Tools | `POST /tools/{tool_name}` — call any registry tool with its JSON input |
| Robots | `GET /robots` · `POST /robots/status` · `GET /robots/{sn}/status` · `/capabilities` · `/work-modes` |
| Maps | `GET /robots/{sn}/maps` · `/maps/{map_id}/canvas` · `/maps/{map_id}/resources` |
| Tasks | `GET/POST /robots/{sn}/task-definitions` · `GET/PUT/DELETE …/{fusion_task_id}` · `POST /robots/{sn}/tasks/{start\|pause\|resume\|stop\|skip}` |
| Navigation | `POST /robots/{sn}/navigation/{go-home\|pause\|resume\|stop}` |
| Commands & reports | `GET /robots/{sn}/commands` · `…/commands/{request_id}` · `GET /robots/{sn}/reports` |
| Schedules | `GET/POST /robots/{sn}/schedules` · `POST …/schedules/simple` · `GET/PUT/DELETE …/schedules/{plan_id}` |
| Agent | `POST /agent/sessions` · `GET/DELETE /agent/sessions/{id}` · `POST …/{id}/messages` (**SSE**) · `POST …/{id}/confirm` |

SSE events from `/messages`: `text_delta` · `tool_call` · `tool_result` · `confirm_required` · `done` · `error`.

```bash
SID=$(curl -s -XPOST -H "X-API-Key: $KEY" localhost:8000/api/v1/agent/sessions | jq -r .session_id)
curl -N -XPOST -H "X-API-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"content":"List my robots and their battery"}' \
  localhost:8000/api/v1/agent/sessions/$SID/messages
```

**H5** (`h5/`, Vue 3 + Vite + Vant): 对话 (streaming chat with tool cards and confirm buttons) · 机器人 (list with online/battery/work-state) · 详情 (maps & canvas, task definitions, quick actions, reports) · 设置 (API base / key). The production build is committed to `src/gs_openapi/server/static/` so `pip install` ships it.

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` | – | **Required.** Gausium application + AccessKey credentials |
| `GS_BASE_URL` | `https://openapi.gs-robot.com/` | Upstream base URL (point at a mock for testing) |
| `GS_HTTP_TIMEOUT` | `30` | HTTP timeout, seconds |
| `GS_ENABLE_LEGACY_TOOLS` | unset | `1` also registers 0.1.x tools as `legacy_*` in the MCP server |
| `GS_SERVER_HOST` / `GS_SERVER_PORT` | `0.0.0.0` / `8000` | HTTP server bind |
| `GS_SERVER_API_KEY` | unset | When set, protected routes require `X-API-Key` |
| `PI_AGENT_PROVIDER` | `anthropic` | `anthropic` or `openai` |
| `PI_AGENT_MODEL` | `claude-opus-5` / `deepseek-chat` | Model ID per provider |
| `ANTHROPIC_API_KEY` | – | Anthropic provider key |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | – | OpenAI-compatible provider |
| `PI_AGENT_AUTO_APPROVE` | `0` | `1` skips dangerous-tool confirmation |
| `PI_AGENT_MAX_TURNS` | `12` | Max tool cycles per user message |

## 📂 Project Layout

```
src/gs_openapi/
├── auth/token_manager.py      OAuth token (ms-epoch expiry, locked refresh)
├── core/                      HTTP client, V3 endpoint registry, errors
├── v3/                        GausiumV3 facade · pydantic models · reference tables
├── tools/                     Tool registry (single source for MCP / Agent / REST)
├── mcp/                       FastMCP server (v3_server.py) + legacy_tools.py
├── agent/                     Pi Agent core, providers, session store, CLI
├── server/                    FastAPI app, routes, SSE, static H5 hosting
└── main.py                    `mcp-gs-robot` stdio entry
h5/                            Vue 3 mobile web app (builds into server/static)
skills/gs-robot/               Agent Skill + references
docs/ARCHITECTURE_V3.md        The contract every module follows
tests/                         48 unit tests (httpx.MockTransport, no network)
```

## 🧑‍💻 Development

```bash
uv sync --extra dev
uv run pytest -q                 # 48 passed
uv run ruff check src tests
cd h5 && npm ci && npm run build # rebuild the H5 into src/gs_openapi/server/static
uv build                         # wheel includes the H5 assets
```

Adding a V3 tool: define the input model + handler in `src/gs_openapi/tools/v3_tools.py` with the `@tool(...)` decorator. MCP, REST and the Agent pick it up automatically; add a row to the table above and a test. Read [`CLAUDE.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CLAUDE.md) for conventions and the [Testing Guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) for curl walkthroughs and MCP Inspector usage.

## 🔁 Migrating from 0.1.x

| 0.1.x | 0.2.0 |
|---|---|
| `get_robot_status_smart`, `get_robot_status` (v1/v2 routing by SN prefix) | `get_robot_status` (V3 snapshot, any series, batch ≤100) |
| `get_task_reports_smart`, `list_robot_task_reports` | `list_task_reports` |
| `create_robot_command` (start/pause/stop) | `start_task` / `pause_task` / `resume_task` / `stop_task`, `navigate_home` |
| `submit_temp_site_task`, `execute_*_workflow` | `create_task_definition` + `start_task`, or `run_cleaning_task` |
| `list_robot_maps` (openapi/v1) | `list_robot_maps` (V3) + `list_task_resources` |

Old tools remain available with `GS_ENABLE_LEGACY_TOOLS=1` under `legacy_*` names. The OAuth `expires_in` bug (treated a ms timestamp as seconds) is fixed — remove any refresh workarounds.

## 📖 Documentation

| Document | Purpose |
|---|---|
| [Architecture contract](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md) | Tool names, REST/SSE protocol, agent interface |
| [V3 API index](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) | Every endpoint with method, path, supported firmware and a link to the official page |
| [Claude Code integration](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md) | MCP setup + Skill |
| [Testing guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) | Unit tests, curl walkthrough, MCP Inspector |
| [Skill README](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md) | Installing the skill in Claude Code / Codex / WorkBuddy |
| [Changelog](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CHANGELOG.md) | Release notes |

## 🤝 Contributing

1. Fork and create a feature branch
2. `uv sync --extra dev`, make your change, add tests
3. `uv run pytest -q && uv run ruff check src tests`
4. Update the docs/tool table if you touched the registry
5. Open a pull request

## 📄 License

MIT — see [LICENSE](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE).

## ⚠️ Disclaimer

This project is an **unofficial, open-source effort for personal research and learning**, built only from Gausium's public OpenAPI V3 documentation. It is not affiliated with, endorsed by, or supported by Gausium. No warranty of any kind; you are responsible for any robot you command. Always validate on simulators or idle machines first, keep credentials out of version control, and remember that a delivered command (`cmdStatus=6`) is not a completed task.

---

<div align="center">

*Made for people who would rather ask their robots than click through consoles.* 🤖✨

</div>
