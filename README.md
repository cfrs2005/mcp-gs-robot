<div align="center">

# 🤖 mcp-gs-robot

**Talk to your Gausium cleaning robots — from Claude, Cursor, a terminal, or your phone.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-gs-robot.svg)](https://pypi.org/project/mcp-gs-robot/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)
[![CI](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![OpenAPI V3](https://img.shields.io/badge/Gausium_OpenAPI-V3-orange.svg)](https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Overview)

MCP server · HTTP/REST server · Saodi 扫地僧 agent (CLI + H5) · Agent Skill<br>
one codebase, one tool registry, built on Gausium OpenAPI V3

[5-minute start](#-5-minute-quick-start) · [Let your AI agent set it up](#-let-your-ai-agent-set-it-up) · [Safety](#-safety-model) · [Cognition & memory](#-saodis-cognition-and-memory) · [Tools](#-tools) · [HTTP API & H5](#-http-api--h5) · [Configuration](#-configuration) · [Troubleshooting](#-troubleshooting) · [中文文档](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README_CN.md)

</div>

> ⚠️ **Disclaimer** — This is an **unofficial, open-source project for personal research and learning.** Not affiliated with, endorsed by, or supported by Gausium (高仙). Use at your own risk — robot commands move physical machines, so test on simulators or idle robots first. Built solely from the public [Gausium OpenAPI V3 documentation](https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Overview).

![H5 app: Saodi chat, fleet, maps and reports](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/h5-showcase.png)

<sub>Screenshots of the built-in H5 app, running against a mock upstream with demo data.</sub>

## 🌟 What is this?

`mcp-gs-robot` wraps the Gausium OpenAPI **V3** (robot status, maps, combined tasks, schedules, commands, reports) in a typed Python client, and exposes it through four entry points that share **one tool registry**:

| | Entry point | Command | Use it when… |
|---|---|---|---|
| 🔌 | **MCP Server** (stdio) | `mcp-gs-robot` | Claude Code, Claude Desktop, Cursor, Cherry Studio or any MCP client should operate robots |
| 🌐 | **HTTP Server** (FastAPI) | `gs-robot-server` | You want REST endpoints, Swagger and the built-in **H5 mobile app** |
| 🧠 | **Saodi 扫地僧** (CLI + H5 chat) | `saodi` | You want a chat assistant that plans and runs robot operations behind confirmation gates, and remembers what it learns |
| 📚 | **Agent Skill** | `skills/gs-robot/` | You want to teach Claude Code / Codex / WorkBuddy the correct operating procedure |

![Architecture](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/architecture.svg)

- **42 tools** — all 36 V3 business endpoints, the legacy robot list, local lookups (`describe_work_state`, `lookup_error_code`), local memory (`remember`) and workflow helpers (`run_cleaning_task`, `wait_for_command`)
- **Typed & tested** — pydantic v2 models, envelope unwrapping, six-digit error codes surfaced as `GausiumAPIError`; offline test suite with a mock HTTP transport
- **Safety first** — every tool that moves a robot or writes data is flagged `dangerous` and needs explicit approval in the Agent, CLI and H5
- **Gets smarter with use** — sessions, tool calls and error threads are kept in a local SQLite file; verified lessons go into a private memory file that every new session loads
- **Provider-agnostic Agent** — Anthropic (default, `claude-opus-5`) or any OpenAI-compatible endpoint (DeepSeek, vLLM, Ollama…); it answers in the language you write in
- **Built strictly on the official docs** — [`docs/apis.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) maps each endpoint to its official page; the full contract is [`docs/ARCHITECTURE_V3.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md)

## 🚀 5-minute quick start

**Prerequisites**: Python 3.12+, [uv](https://docs.astral.sh/uv/), and Gausium open-platform credentials (an application plus an AccessKey from the [Gausium Developer Center](https://developer.gs-robot.com/)). Node 18+ is only needed if you want to rebuild the H5 app — a production build is already committed.

**1 · Install**

```bash
git clone https://github.com/cfrs2005/mcp-gs-robot.git
cd mcp-gs-robot
uv sync --extra dev
```

(Or `pip install mcp-gs-robot` if you only need the commands; the wheel ships the H5 build and the skill.)

**2 · Configure** — `cp .env.example .env`, then fill in:

| What | Variables |
|---|---|
| Gausium credentials | `GS_CLIENT_ID`, `GS_CLIENT_SECRET`, `GS_OPEN_ACCESS_KEY` (the **AccessKeySecret**, not the AccessKeyID) |
| Environment | `GS_BASE_URL` — production `https://openapi.gs-robot.com/`, test `https://openapi.dev.gs-robot.com/` |
| HTTP server key | `GS_SERVER_API_KEY` — any long random string; the H5 and REST clients send it as `X-API-Key` |
| LLM (pick one) | Anthropic: `SAODI_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` · OpenAI-compatible: `SAODI_PROVIDER=openai` + `OPENAI_BASE_URL` + `OPENAI_API_KEY` + `SAODI_MODEL` |

`.env` is read from the **current working directory** by every entry point, is git-ignored, and must never be committed. Real environment variables take precedence over `.env`.

**3 · Run an entry point** (from the repository root)

| Entry point | Command | Then |
|---|---|---|
| 🔌 MCP (stdio) | `claude mcp add gs-robot -- uv --directory "$PWD" run mcp-gs-robot` | Ask your MCP client *"List my robots and show battery and work state"* |
| 🌐 REST + H5 | `uv run gs-robot-server` | Open `http://localhost:8000/` → **Settings** → paste `GS_SERVER_API_KEY` → Save. Swagger: `http://localhost:8000/docs` |
| 🧠 Saodi CLI | `uv run saodi` | Chat in the terminal; dangerous steps ask `[y/N]` |
| 📚 Skill | `cp -r skills/gs-robot ~/.claude/skills/gs-robot` | Also mount the MCP server (row 1); the skill teaches the procedure |

Check that the server is up: `curl -s http://127.0.0.1:8000/api/v1/health` → `{"status":"ok", …, "auth_required":true}`. `auth_required: true` means the H5 needs the key before anything else works.

`uv run saodi --show-context` prints Saodi's full system prompt without any key — a quick way to confirm the install.

## 🤝 Let your AI agent set it up

Paste this into Claude Code, Codex or Cursor (agent mode). It installs, configures, tests and smoke-tests the project **with read-only calls only**. The same prompt, with a Chinese version, is in [`docs/AGENT_SETUP_PROMPT.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/AGENT_SETUP_PROMPT.md).

```text
Set up mcp-gs-robot (an unofficial MCP / REST / agent wrapper for the Gausium OpenAPI V3) on this
machine. Work step by step, show me each command's result, and stop at the first failure.

Hard rules
- Robots are physical machines. Call read-only tools only. Never call a tool marked dangerous
  (anything that creates, updates or deletes tasks or schedules, starts / pauses / resumes / stops /
  skips tasks, navigates, runs a cleaning workflow, or writes memory with `remember`).
- Never print, echo, log or commit credentials. Write them only into .env with your file-edit tool
  (not via shell echo), never paste them back to me, and confirm .env is git-ignored.

Steps
1. Prerequisites: `python3 --version` (3.12+) and `uv --version`. `node --version` (18+) only
   matters for step 5.
2. `git clone https://github.com/cfrs2005/mcp-gs-robot.git && cd mcp-gs-robot && uv sync --extra dev`
3. `cp .env.example .env`. Ask me for GS_CLIENT_ID, GS_CLIENT_SECRET and GS_OPEN_ACCESS_KEY (the
   AccessKeySecret, not the AccessKeyID), and whether to use production
   (https://openapi.gs-robot.com/) or test (https://openapi.dev.gs-robot.com/) for GS_BASE_URL.
   Ask which LLM provider I use: Anthropic (SAODI_PROVIDER=anthropic + ANTHROPIC_API_KEY) or an
   OpenAI-compatible endpoint (SAODI_PROVIDER=openai + OPENAI_BASE_URL + OPENAI_API_KEY +
   SAODI_MODEL). Generate GS_SERVER_API_KEY yourself with
   `python3 -c "import re,secrets,pathlib;p=pathlib.Path('.env');p.write_text(re.sub(r'(?m)^GS_SERVER_API_KEY=.*$','GS_SERVER_API_KEY='+secrets.token_urlsafe(32),p.read_text()))"` (it rewrites the line in .env in place and never prints the key; I will read it from .env myself).
   Then run `git check-ignore .env` (it must print .env) and `git status --short` (.env must not
   appear).
4. `uv run pytest -q` and `uv run ruff check src tests`; both must pass.
5. If Node 18+ is available: `cd h5 && npm ci && npm run build && cd ..`. Otherwise skip; a
   prebuilt H5 is already in src/gs_openapi/server/static/.
6. Start the server in the background with its output in a log file:
   `uv run gs-robot-server > server.log 2>&1 &`
7. `curl -s http://127.0.0.1:8000/api/v1/health` must return "status":"ok" and
   "auth_required":true.
8. Tell me to open http://localhost:8000/, go to Settings, paste the GS_SERVER_API_KEY value from
   .env and press Save (it should report the connection as OK). Do not show me the key yourself.
9. Read-only smoke test. Load the key without printing it:
   `KEY=$(grep '^GS_SERVER_API_KEY=' .env | cut -d= -f2-)`
   - `curl -s -X POST -H "X-API-Key: $KEY" -H 'Content-Type: application/json'
     -d '{"page":1,"page_size":5}' http://127.0.0.1:8000/api/v1/tools/list_robots`
   - pick one robot from that list with "online": true and call get_robot_status the same way
     with body {"robot_sn_list":["<that SN>"]}.
   Error meanings: 401 = wrong or missing X-API-Key; 110003 = these credentials are not bound to
   that robot (not "no data"); 230003 = robot offline; 100026 = rate limited, slow down.
10. Report: tool versions, pytest / ruff results, the health response, how many robots are
    online / offline, and any error as `<code> <msg>`. Leave out secrets and trace IDs.
```

## 🧭 Entry points in detail

<details open>
<summary><b>🔌 MCP Server — Claude Code / Claude Desktop / Cursor</b></summary>

From a clone (reads `.env` in the repository):

```bash
claude mcp add gs-robot -- uv --directory /path/to/mcp-gs-robot run mcp-gs-robot
```

From `pip install mcp-gs-robot`, pass credentials explicitly — in `claude_desktop_config.json` / Cursor MCP settings:

```json
{
  "mcpServers": {
    "gs-robot": {
      "command": "mcp-gs-robot",
      "env": { "GS_CLIENT_ID": "…", "GS_CLIENT_SECRET": "…", "GS_OPEN_ACCESS_KEY": "…" }
    }
  }
}
```

Transport is **stdio**. MCP hosts run tools directly, so keep your host's own tool-approval prompts on for dangerous tools. Set `GS_ENABLE_LEGACY_TOOLS=1` to also expose the 0.1.x tools as `legacy_*`.

</details>

<details>
<summary><b>🌐 HTTP Server + H5 mobile app</b></summary>

```bash
uv run gs-robot-server              # http://0.0.0.0:8000 (GS_SERVER_HOST / GS_SERVER_PORT)
```

- **H5 app** — open `http://localhost:8000/` on your phone or in a browser, then fill in the API key under **Settings**
- **Swagger** — `http://localhost:8000/docs`
- **Docker** — `cp .env.example .env && $EDITOR .env && docker compose up -d` (serves on `:8000`)

</details>

<details>
<summary><b>🧠 Saodi (扫地僧) — chat in the terminal</b></summary>

```bash
uv run saodi                                   # provider and keys from .env
uv run saodi --robot <robot-sn>                # scope the session to one robot
uv run saodi --show-context                    # print the system prompt and exit (no key needed)
```

```
you> Is the lobby robot free? Enough battery for a full dust-push?
⚙ get_robot_status(robot_sn_list=["<robot-sn>"])
Online, 82% battery, IDLE on map "Lobby" — good to go.
you> Start the lobby dust-push task
⚙ list_task_definitions(...)
Approve start_task robot_sn=<robot-sn> fusion_task_id=…? [y/N] y
⚙ start_task(...)  ⚙ wait_for_command(...)
Command delivered (cmdStatus=6); it is not finished yet — I'll check workState again in ~30 s.
```

Other subcommands (no LLM key, no upstream calls):

```bash
uv run saodi memory                            # path and content of the local memory file
uv run saodi memory add "<lesson>" [--scope S] # add one lesson by hand
uv run saodi memory edit                       # open it in $VISUAL / $EDITOR
uv run saodi errors [--status open] [--json]   # error threads from the tool-call log
uv run saodi errors show <id>                  # one thread with its recent calls
uv run saodi errors promote <id>               # turn a thread into a memory lesson
```

> Renamed from *Pi Agent* after 0.2.0: the old `pi-agent` command and `PI_AGENT_*` variables still work for one release and print a deprecation warning.

</details>

<details>
<summary><b>📚 Agent Skill — Claude Code / Codex / WorkBuddy</b></summary>

```bash
cp -r skills/gs-robot ~/.claude/skills/gs-robot     # Claude Code (user scope)
cp -r skills/gs-robot ~/.codex/skills/gs-robot      # Codex CLI
```

The skill encodes the safe operating procedure (status → capabilities → resources → task definition → start → poll) and ships reference tables for work states, command types and task-start error codes. See [`skills/gs-robot/README.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md).

</details>

## 🔒 Safety model

Tools that move a robot or write data are registered with `dangerous=True`. Saodi never runs them on its own: it emits `confirm_required` and waits — `[y/N]` in the terminal, buttons in the H5, `POST …/confirm` over REST. A rejected call never reaches the robot (or the memory file).

![Dangerous tool confirmation flow](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/confirm-flow.svg)

Keep in mind:

- **Delivered is not finished.** `cmdStatus=6` means the robot received the command; follow up with `get_robot_status` or task reports.
- **REST executes directly.** `POST /api/v1/tools/{name}` treats the caller as already having confirmed — gate it in your own client. `SAODI_AUTO_APPROVE=1` disables the Agent gate (not recommended).

For the common "clean these areas" case, `run_cleaning_task` bundles the whole procedure into one confirmed call:

![run_cleaning_task workflow](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/cleaning-workflow.svg)

## 🧠 Saodi's cognition and memory

Every new session gets one system prompt, assembled in this order and fixed for the session (`saodi --show-context` prints it):

| Layer | Where | Maintained by | Shared? |
|---|---|---|---|
| **Soul** — identity, voice (answers in your language), safety rules, when to propose `remember` | `src/gs_openapi/agent/soul.md` | project maintainers | open source |
| **Knowledge** — domain model, operating procedure, work-state table | `skills/gs-robot/` (`references/domain.md`, `SKILL.md`, `references/work-states.md`) — the same files the Agent Skill uses | project maintainers | open source |
| **Memory** — field-tested call experience | `skills/gs-robot/references/experience.md` | contributors, via pull requests | open source |
| **Local memory** — lessons learned on your machine | `$SAODI_DATA_DIR/memory.md` (default `~/.saodi/memory.md`) | you and Saodi (`remember`, `saodi memory`, `saodi errors promote`) | private, never in git |
| **Private context** — notes you keep elsewhere | `$SAODI_CONTEXT_DIR/*.md` (sorted by name) | you | private |

The official error-code table (`skills/gs-robot/references/error-codes.md`, ~23 KB) is **not** loaded into every prompt: Saodi calls the read-only `lookup_error_code` tool when it meets a code it does not know, and is told not to guess. The whole prompt is capped by `SAODI_CONTEXT_MAX_CHARS` (default 60000); when it overflows, the **oldest local memory entries are dropped first** and a WARNING says how many.

**How it gets smarter**

1. **`remember` in chat.** When Saodi learns something verified and reusable — what an error code means in practice, a robot's lasting quirk, your preferences — it proposes `remember(lesson)`. That writes a file, so it asks for confirmation like any dangerous tool. On approval it appends `- [YYYY-MM-DD] lesson` to `memory.md`; duplicates are skipped and anything that looks like a credential (token / secret / Bearer / long random strings) is refused. It does not remember one-off data (today's battery, a single snapshot) or guesses. The next session loads the new line.
2. **From errors to lessons.** Every tool call is logged locally; failures are folded into error threads. `saodi errors` lists them, `PATCH /api/v1/errors/threads/{id}` (try it in Swagger at `/docs`) lets you set the status, category and a `note`, and `saodi errors promote <id>` writes the note (or, if empty, the category and sample message) into `memory.md` and marks the thread as promoted.
3. **By hand.** `saodi memory add "…"` or `saodi memory edit`.
4. **Back to everyone.** If a lesson is general, propose it for `experience.md` in a pull request. Writing rule: general behaviour and how to handle it only — **no robot SNs, trace IDs, request IDs, accounts, credentials, customer or site names**.

## 🧰 Tools

All 42 tools are defined once in `gs_openapi/tools/` and exposed identically to MCP, the Agent and REST (`POST /api/v1/tools/{name}`). Inputs are `snake_case`; the registry maps them to V3 `camelCase`. **⚠️ = dangerous.**

| Category | Tools |
|---|---|
| **Robots** | `list_robots` · `get_robot_status` · `describe_work_state` · `get_robot_capabilities` |
| **Maps** | `list_robot_maps` · `get_map_canvas` · `list_charging_positions` · `list_map_resources` · `list_task_resources` |
| **Tasks** | `list_work_modes` · `list_task_definitions` · `get_task_definition` · `create_task_definition` ⚠️ · `update_task_definition` ⚠️ · `delete_task_definition` ⚠️ · `start_task` ⚠️ · `pause_task` ⚠️ · `resume_task` ⚠️ · `stop_task` ⚠️ · `skip_task_item` ⚠️ |
| **Schedules** | `list_schedules` · `get_schedule` · `get_schedule_calendar` · `list_schedule_pre_tasks` · `create_simple_schedule` ⚠️ · `update_simple_schedule` ⚠️ · `delete_simple_schedule` ⚠️ · `create_schedule` ⚠️ · `update_schedule` ⚠️ · `delete_schedule` ⚠️ |
| **Commands** | `get_command_status` · `list_command_history` · `navigate_home` ⚠️ · `pause_navigation` ⚠️ · `resume_navigation` ⚠️ · `stop_navigation` ⚠️ |
| **Reports** | `list_task_reports` · `get_task_report_map_images` |
| **Workflows** | `wait_for_command` · `run_cleaning_task` ⚠️ |
| **Reference** | `lookup_error_code` (local, read-only) |
| **Memory** | `remember` ⚠️ (writes the local memory file) |

<details>
<summary><b>Inputs for each tool</b></summary>

**Robots & Maps**

| Tool | Required | Optional | Notes |
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

**Tasks**

| Tool | Required | Optional | |
|---|---|---|---|
| `list_work_modes` | `robot_sn` | | |
| `list_task_definitions` | `robot_sn` | `page`, `pagesize`, `site_id`, `task_name` | |
| `get_task_definition` | `robot_sn`, `fusion_task_id` | | |
| `create_task_definition` | `robot_sn`, `task_name`, `work_mode`, `map_resource_list` | `loop_count`, `site_id`, `task_advance_config` | ⚠️ |
| `update_task_definition` | `robot_sn`, `fusion_task_id` | same as create | ⚠️ |
| `delete_task_definition` | `robot_sn`, `fusion_task_id` | | ⚠️ |
| `start_task` | `robot_sn`, `fusion_task_id` | `loop_count` | ⚠️ returns `requestId`, `taskInstanceId` |
| `pause_task` / `resume_task` / `stop_task` / `skip_task_item` | `robot_sn` | | ⚠️ |

**Schedules**

| Tool | Required | |
|---|---|---|
| `create_simple_schedule` | `robot_sn`, `task_name`, `site_mode`, `work_mode`, `map_resource_list`, `plan_execute_type`, `plan_repeat_type`, `plan_start_date`, `plan_start_time` | ⚠️ |
| `update_simple_schedule` / `delete_simple_schedule` | `robot_sn`, `plan_uuid`, `year`, `month`, `day_of_month`, `operation_type` | ⚠️ |
| `create_schedule` / `update_schedule` / `delete_schedule` | standard schedule fields (see [docs](https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Overview)) | ⚠️ |
| `list_schedules` | `robot_sn` | |
| `get_schedule` | `robot_sn`, `plan_uuid`, `year`, `month`, `day_of_month` | |
| `get_schedule_calendar` | `robot_sn`, `year_month` | |
| `list_schedule_pre_tasks` | `robot_sn`, `date` | |

**Commands, Reports, Workflows, Reference & Memory**

| Tool | Required | Optional | |
|---|---|---|---|
| `get_command_status` | `robot_sn`, `request_id` | | `cmdStatus=6` = delivered, **not** finished |
| `list_command_history` | `robot_sn` | `page`, `pagesize`, `cmd_status`, `command_type` | |
| `navigate_home` | `robot_sn`, `map_id` | `map_resource_id` | ⚠️ |
| `pause_navigation` / `resume_navigation` / `stop_navigation` | `robot_sn` | | ⚠️ |
| `list_task_reports` | `robot_sn` | `page`, `pagesize`, `end_time_min`, `end_time_max` | |
| `get_task_report_map_images` | `task_report_id` | `robot_sn` | |
| `wait_for_command` | `robot_sn`, `request_id` | `timeout_seconds` | Polls until a terminal `cmdStatus` |
| `run_cleaning_task` | `robot_sn`, `task_name`, `map_id`, `resource_ids` | `mode`, `strength`, `loop_count`, `wait_seconds` | ⚠️ capabilities → resources → create → start → poll |
| `lookup_error_code` | `code` (3–10 digits) | | Matching rows from `error-codes.md` and entries from `experience.md`; `found: false` + a "do not guess" hint otherwise |
| `remember` | `lesson` | `scope` | ⚠️ appends `- [YYYY-MM-DD] lesson` to `$SAODI_DATA_DIR/memory.md`; de-duplicated, credential-looking text refused |

</details>

Regenerate the list from the registry:

```bash
uv run python -c "from gs_openapi.tools.registry import REGISTRY; [print(t.category, t.name, '⚠️' if t.dangerous else '') for t in REGISTRY.values()]"
```

## 🌐 HTTP API & H5

Base prefix `/api/v1`. `GET /health` is public; everything else requires `X-API-Key` when `GS_SERVER_API_KEY` is set. Errors share one envelope, `{"error": {"code", "message", "trace_id"}}`; upstream V3 errors become HTTP 502 carrying the business code.

| Area | Routes |
|---|---|
| Health & auth | `GET /health` (public; `auth_required` tells clients a key is needed, never the key) · `GET /auth/check` (validates the key, no upstream call) |
| Tools | `POST /tools/{tool_name}` — call any registry tool with its JSON input |
| Robots | `GET /robots` · `POST /robots/status` · `GET /robots/{sn}/status` · `/capabilities` · `/work-modes` |
| Maps | `GET /robots/{sn}/maps` · `/maps/{map_id}/canvas` · `/maps/{map_id}/resources` |
| Tasks | `GET/POST /robots/{sn}/task-definitions` · `GET/PUT/DELETE …/{fusion_task_id}` · `POST /robots/{sn}/tasks/{start\|pause\|resume\|stop\|skip}` |
| Navigation | `POST /robots/{sn}/navigation/{go-home\|pause\|resume\|stop}` |
| Commands & reports | `GET /robots/{sn}/commands` · `…/commands/{request_id}` · `GET /robots/{sn}/reports` |
| Schedules | `GET/POST /robots/{sn}/schedules` · `POST …/schedules/simple` · `GET/PUT/DELETE …/schedules/{plan_id}` |
| Agent | `GET/POST /agent/sessions` · `GET/DELETE /agent/sessions/{id}` · `POST …/{id}/messages` (**SSE**) · `POST …/{id}/confirm` |
| Error threads | `GET /errors/threads` · `GET/PATCH /errors/threads/{id}` |

SSE events from `/messages`: `text_delta` · `tool_call` · `tool_result` · `confirm_required` · `done` · `error`. Sessions are stored in SQLite, so a conversation survives a server restart.

```bash
KEY=$(grep '^GS_SERVER_API_KEY=' .env | cut -d= -f2-)
SID=$(curl -s -XPOST -H "X-API-Key: $KEY" localhost:8000/api/v1/agent/sessions | jq -r .session_id)
curl -N -XPOST -H "X-API-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"content":"List my robots and their battery"}' \
  localhost:8000/api/v1/agent/sessions/$SID/messages
```

**H5** (`h5/`, Vue 3 + Vite + Vant): **Chat** (streaming Markdown, HTML preview, a tool-call timeline, confirm buttons and a history drawer), **Robots** (fleet list with online / offline / unreachable states, battery and work state), **Detail** (maps & canvas, task definitions, quick actions, reports; offline robots get a banner instead of errors) and **Settings** (API base, API key, language). When the server needs a key and none is saved, the H5 sends you to Settings. The production build is committed to `src/gs_openapi/server/static/`, so `pip install` ships it.

### 🌍 Languages

- **H5**: English and 中文, switchable under Settings → Language (the first visit follows the browser language).
- **Saodi**: replies in the language you write in; field names such as `workState` or `cmdStatus` stay in English.
- **Docs**: English is the primary language; [README_CN.md](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README_CN.md) mirrors this file in Chinese. Tool descriptions are bilingual.

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` | – | **Required.** Gausium application + AccessKey credentials (`GS_OPEN_ACCESS_KEY` is the AccessKeySecret) |
| `GS_BASE_URL` | `https://openapi.gs-robot.com/` | Upstream base URL; test environment `https://openapi.dev.gs-robot.com/`, or a mock |
| `GS_HTTP_TIMEOUT` | `30` | HTTP timeout, seconds |
| `GS_ENABLE_LEGACY_TOOLS` | unset | `1` also registers 0.1.x tools as `legacy_*` in the MCP server |
| `GS_SERVER_HOST` / `GS_SERVER_PORT` | `0.0.0.0` / `8000` | HTTP server bind |
| `GS_SERVER_API_KEY` | unset | When set, protected routes require `X-API-Key` |
| `SAODI_PROVIDER` | `anthropic` | `anthropic` or `openai` |
| `SAODI_MODEL` | `claude-opus-5` / `deepseek-chat` | Model ID per provider |
| `ANTHROPIC_API_KEY` | – | Anthropic provider key |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | – | OpenAI-compatible provider |
| `SAODI_AUTO_APPROVE` | `0` | `1` skips dangerous-tool confirmation (including `remember`) |
| `SAODI_MAX_TURNS` | `12` | Max tool cycles per user message (tool results are truncated at 20k chars) |
| `SAODI_DATA_DIR` | `~/.saodi` | Local data: `saodi.sqlite` (sessions, tool-call log, error threads) and `memory.md` (local memory) |
| `SAODI_CONTEXT_DIR` | unset | Directory of private `*.md` notes appended to the system prompt |
| `SAODI_CONTEXT_MAX_CHARS` | `60000` | System prompt length cap; oldest local memory entries go first, then truncation, with a WARNING |

Deprecated names, read for one more release when the new name is unset (each prints one WARNING with the name only):

| New | Deprecated |
|---|---|
| `SAODI_PROVIDER` | `PI_AGENT_PROVIDER` |
| `SAODI_MODEL` | `PI_AGENT_MODEL` |
| `SAODI_AUTO_APPROVE` | `PI_AGENT_AUTO_APPROVE` |
| `SAODI_MAX_TURNS` | `PI_AGENT_MAX_TURNS` |
| `saodi` (command) | `pi-agent` |

## 🩺 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| **401** in the H5 or from curl | `GS_SERVER_API_KEY` is set but the client sent no / a wrong `X-API-Key` | H5: Settings → paste the key → Save (it checks `/api/v1/auth/check`). curl: add `-H "X-API-Key: …"`. `GET /api/v1/health` shows `auth_required` |
| **110003** `Robot is not bound to the current user.` | Your open-platform application is not bound to this robot (or lacks permission for this data) | This is **not** "no data". Check whether the SN appears in `list_robots`; if not, bind the robot to the application on the open platform. Report endpoints can say 110003 even when status works |
| **230003** `Robot … routing failed.` | Robot offline / long disconnected from the cloud | Check `onlineStatus` / the `online` field of `list_robots`; retrying other endpoints will not help. One such robot fails a whole batch status call; the REST robot list already falls back to per-robot queries |
| **100026** | Rate limit (~20 calls/s) | Slow down; avoid concurrent bursts |
| **422** with correct parameters | Possibly upstream field drift (the response no longer matches the local model) | Run `uv run saodi errors` — a `response_model` / `our_bug` thread points at the model to fix; please open an issue |
| Credentials "missing" although `.env` exists | `.env` is read from the **current working directory**; real environment variables win over it | Run commands from the directory holding `.env` (for MCP: `uv --directory <repo> run mcp-gs-robot`), or pass the variables in the MCP `env` block; check for stale exported variables with `env \| grep '^GS_'` |
| `PI_AGENT_* is deprecated` warnings | Old variable names in `.env` | Rename them to `SAODI_*` |

## 🧑‍💻 Development

```
src/gs_openapi/
├── auth/token_manager.py      OAuth token (ms-epoch expiry, locked refresh)
├── core/                      HTTP client, V3 endpoint registry, errors
├── v3/                        GausiumV3 facade · pydantic models · reference tables
├── tools/                     Tool registry (single source for MCP / Agent / REST) + knowledge tools
├── mcp/                       FastMCP server (v3_server.py) + legacy_tools.py
├── agent/                     Saodi core, soul.md, prompt builder, providers, sessions, CLI
├── store/                     SQLite sessions / tool-call log / error threads, local memory.md
├── server/                    FastAPI app, routes, SSE, static H5 hosting
└── main.py                    `mcp-gs-robot` stdio entry
h5/                            Vue 3 mobile web app (builds into server/static)
skills/gs-robot/               Agent Skill + references (also Saodi's Knowledge / Memory)
docs/ARCHITECTURE_V3.md        The contract every module follows
tests/                         Offline tests (httpx.MockTransport, no network)
```

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check src tests
cd h5 && npm ci && npm run build    # rebuild the H5 into src/gs_openapi/server/static
uv build                            # wheel includes the H5 assets and the skill
```

To add a V3 tool, define the input model and handler in `src/gs_openapi/tools/v3_tools.py` with `@tool(...)`; MCP, REST and the Agent pick it up automatically. Add a test and a row to the tool tables. Conventions are in [`CLAUDE.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CLAUDE.md); curl walkthroughs and MCP Inspector usage are in the [Testing Guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md).

<details>
<summary><b>🔁 Migrating from 0.1.x</b></summary>

| 0.1.x | 0.2.0+ |
|---|---|
| `get_robot_status_smart`, `get_robot_status` (v1/v2 routing by SN prefix) | `get_robot_status` (V3 snapshot, any series, batch ≤100) |
| `get_task_reports_smart`, `list_robot_task_reports` | `list_task_reports` |
| `create_robot_command` (start/pause/stop) | `start_task` / `pause_task` / `resume_task` / `stop_task`, `navigate_home` |
| `submit_temp_site_task`, `execute_*_workflow` | `create_task_definition` + `start_task`, or `run_cleaning_task` |
| `list_robot_maps` (openapi/v1) | `list_robot_maps` (V3) + `list_task_resources` |

Old tools remain available under `legacy_*` names with `GS_ENABLE_LEGACY_TOOLS=1`. The OAuth `expires_in` bug (a millisecond timestamp treated as seconds) is fixed, so remove any refresh workarounds.

</details>

## 📖 Documentation

| Document | Purpose |
|---|---|
| [Architecture contract](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md) | Tool names, REST/SSE protocol, agent interface, cognition layers, local storage |
| [Agent setup prompt](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/AGENT_SETUP_PROMPT.md) | Copy-paste prompt for Claude Code / Codex / Cursor (English + 中文) |
| [V3 API index](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) | Every endpoint with method, path, supported firmware and a link to the official page |
| [Claude Code integration](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md) | MCP setup + Skill |
| [Testing guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) | Unit tests, curl walkthrough, MCP Inspector |
| [Skill README](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md) | Installing the skill in Claude Code / Codex / WorkBuddy |
| [Changelog](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CHANGELOG.md) | Release notes |

## 🤝 Contributing

Fork, create a feature branch, `uv sync --extra dev`, make your change with tests, run `uv run pytest -q && uv run ruff check src tests`, update the tool tables if you touched the registry, and open a pull request. Experience for `experience.md` is welcome — general behaviour only, with no SNs, trace IDs, accounts, credentials or customer / site names.

## 📄 License

MIT — see [LICENSE](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE).

## ⚠️ Disclaimer

This project is an **unofficial, open-source effort for personal research and learning**, built only from Gausium's public OpenAPI V3 documentation. It is not affiliated with, endorsed by, or supported by Gausium. No warranty of any kind; you are responsible for any robot you command. Always validate on simulators or idle machines first, keep credentials out of version control, and remember that a delivered command (`cmdStatus=6`) is not a completed task.

<div align="center">

*Made for people who would rather ask their robots than click through consoles.* 🤖✨

</div>
