# mcp-gs-robot · OpenAPI V3

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/) [![PyPI](https://img.shields.io/pypi/v/mcp-gs-robot)](https://pypi.org/project/mcp-gs-robot/) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE) [![CI](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml) · [中文](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README_CN.md)

> ⚠️ **Disclaimer**: This is an unofficial, open-source project maintained for personal research and learning. It is not affiliated with, endorsed by, or supported by Gausium (高仙). Use at your own risk. Robot commands can move physical machines: test on simulators or idle robots first. This project relies on the public Gausium OpenAPI V3 documentation.

## What it is

One repository provides four entry points for Gausium robot operations: an MCP stdio server, a Pi Agent CLI (Anthropic or OpenAI-compatible models), a FastAPI REST/SSE server with H5 web interface, and a reusable Agent Skill. All four use the shared V3 tool registry; `list_robots` uses legacy v1alpha1 because V3 has no robot-list endpoint. Installation includes server and agent runtime dependencies; no extra is needed.

## Architecture

![Four entry points sharing the V3 tool registry](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/images/architecture.svg)

The registry maps snake_case tool inputs to the V3 client, HTTP client and token manager. See the [architecture contract](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md).

## Quick start

Requires Python 3.12+ and your own Gausium OpenAPI credentials. Install and supply credentials via the environment (never commit them):

```sh
pip install mcp-gs-robot
export GS_CLIENT_ID="<client-id>"
export GS_CLIENT_SECRET="<client-secret>"
export GS_OPEN_ACCESS_KEY="<access-key>"
```

### MCP (stdio)

```sh
mcp-gs-robot
# Register the installed executable; it inherits credentials from your environment:
claude mcp add gs-robot -- mcp-gs-robot
```

The MCP process uses stdio; it is not the HTTP server. See the [Claude Code integration guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md).

### HTTP + H5

```sh
gs-robot-server
# Open http://localhost:8000/ in your browser
```

For local development, build the H5 before starting the server (`cd h5 && npm ci && npm run build`); published wheels include its static assets. FastAPI Swagger is at `http://localhost:8000/docs`. If `GS_SERVER_API_KEY` is set, pass `X-API-Key` for API routes and enter the key in H5 Settings. Expose the server only behind trusted networking/HTTPS.

### Pi Agent CLI

```sh
export ANTHROPIC_API_KEY="<anthropic-key>"  # default provider
pi-agent --robot "<robot-sn>"
# Or set PI_AGENT_PROVIDER=openai, OPENAI_BASE_URL and OPENAI_API_KEY.
```

Dangerous operations require terminal confirmation by default.

### Agent Skill

```sh
# From the repository root after cloning it:
mkdir -p ~/.claude/skills
cp -r skills/gs-robot ~/.claude/skills/gs-robot
```

Mount the MCP server as above and see the [Skill installation guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md) for Codex/WorkBuddy variants.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GS_CLIENT_ID` | Yes for live API | OpenAPI client ID |
| `GS_CLIENT_SECRET` | Yes for live API | OpenAPI client secret |
| `GS_OPEN_ACCESS_KEY` | Yes for live API | OpenAPI access key |
| `GS_BASE_URL` | No | Upstream API URL; default `https://openapi.gs-robot.com/` (can point to a local mock) |
| `GS_HTTP_TIMEOUT` | No | HTTP timeout in seconds; default `30` |
| `GS_SERVER_API_KEY` | No | When set, protected HTTP routes require `X-API-Key` |
| `GS_SERVER_HOST` | No | Bind address; default `0.0.0.0` |
| `GS_SERVER_PORT` | No | Port; default `8000` |
| `PI_AGENT_PROVIDER` | No | `anthropic` (default) or `openai` |
| `PI_AGENT_MODEL` | No | Defaults: `claude-opus-5` (Anthropic), `deepseek-chat` (OpenAI-compatible) |
| `ANTHROPIC_API_KEY` | Anthropic provider | LLM provider key |
| `OPENAI_API_KEY` | OpenAI provider | OpenAI-compatible provider key |
| `OPENAI_BASE_URL` | OpenAI provider | OpenAI-compatible base URL |
| `PI_AGENT_AUTO_APPROVE` | No | `1` skips agent confirmation; leave unset for safety |
| `PI_AGENT_MAX_TURNS` | No | Agent tool cycles per turn; default `12` |

## MCP tools

Generated from `REGISTRY` in `src/gs_openapi/tools/registry.py` using `uv run python -c 'from gs_openapi.tools.registry import REGISTRY; [print(t.name, t.category, t.dangerous, t.description) for t in REGISTRY.values()]'` (40 tools; bilingual descriptions are the registry text). Dangerous means the Agent requires confirmation; REST tool calls execute immediately.

| Tool | Category | Dangerous | Description |
|---|---|---|---|
| `list_robots` | robots | No | 列出机器人 / List robots |
| `get_robot_status` | robots | No | 查询机器人状态 / Get robot status |
| `describe_work_state` | robots | No | 解释工作状态 / Describe robot work state |
| `get_robot_capabilities` | robots | No | 查询机器人任务能力 / Get task capabilities |
| `list_robot_maps` | maps | No | 列出机器人地图 / List robot maps |
| `get_map_canvas` | maps | No | 查询地图画布 / Get map canvas |
| `list_charging_positions` | maps | No | 列出充电点 / List charging positions |
| `list_map_resources` | maps | No | 列出地图资源 / List map resources |
| `list_task_resources` | maps | No | 查询任务资源 / List task resources |
| `list_work_modes` | tasks | No | 查询工作模式 / List work modes |
| `list_task_definitions` | tasks | No | 分页查询任务定义 / List task definitions |
| `get_task_definition` | tasks | No | 查询任务定义 / Get task definition |
| `create_task_definition` | tasks | Yes | 创建任务定义 / Create task definition |
| `update_task_definition` | tasks | Yes | 更新任务定义 / Update task definition |
| `delete_task_definition` | tasks | Yes | 删除任务定义 / Delete task definition |
| `start_task` | tasks | Yes | 启动任务 / Start task |
| `pause_task` | tasks | Yes | 暂停任务 / Pause task |
| `resume_task` | tasks | Yes | 继续任务 / Resume task |
| `stop_task` | tasks | Yes | 停止任务 / Stop task |
| `skip_task_item` | tasks | Yes | 跳过任务项 / Skip task item |
| `create_simple_schedule` | schedules | Yes | 创建简易排班 / Create simple schedule |
| `update_simple_schedule` | schedules | Yes | 更新简易排班 / Update simple schedule |
| `delete_simple_schedule` | schedules | Yes | 删除简易排班 / Delete simple schedule |
| `create_schedule` | schedules | Yes | 创建标准排班 / Create schedule |
| `update_schedule` | schedules | Yes | 更新标准排班 / Update schedule |
| `delete_schedule` | schedules | Yes | 删除标准排班 / Delete schedule |
| `list_schedules` | schedules | No | 列出排班 / List schedules |
| `get_schedule` | schedules | No | 查询排班详情 / Get schedule |
| `get_schedule_calendar` | schedules | No | 查询月度排班 / Get schedule calendar |
| `list_schedule_pre_tasks` | schedules | No | 查询每日预任务 / List schedule pre-tasks |
| `get_command_status` | commands | No | 查询命令投递状态 / Get command delivery status |
| `list_command_history` | commands | No | 查询命令历史 / List command history |
| `navigate_home` | commands | Yes | 导航回充电点 / Navigate home |
| `pause_navigation` | commands | Yes | 暂停导航 / Pause navigation |
| `resume_navigation` | commands | Yes | 继续导航 / Resume navigation |
| `stop_navigation` | commands | Yes | 停止导航 / Stop navigation |
| `list_task_reports` | reports | No | 分页查询任务报告 / List task reports |
| `get_task_report_map_images` | reports | No | 查询报告地图图像 / Get report map images |
| `wait_for_command` | workflows | No | 等待命令投递终态 / Wait for command delivery |
| `run_cleaning_task` | workflows | Yes | 创建并启动清洁任务 / Create and start cleaning task |

## REST API

`GET /api/v1/health` is public. Protected routes include `GET /api/v1/robots`, `POST /api/v1/robots/status`, `GET /api/v1/robots/{sn}/status`, `POST /api/v1/tools/{tool_name}` (JSON tool inputs), and `POST /api/v1/agent/sessions` followed by `POST /api/v1/agent/sessions/{id}/messages` (SSE). See [the server guide](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md), [V3 upstream endpoint index](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md), and live FastAPI Swagger at `http://localhost:8000/docs` for all routes. SSE is for Agent chat, not MCP transport.

## Security

Agent/Skill dangerous tools require explicit approval before any physical movement or mutating operation; `PI_AGENT_AUTO_APPROVE=1` bypasses this and should not be used casually. Direct REST calls execute without an additional confirmation gate; authenticate callers and confirm actions client-side. Never commit credentials or send them in logs. Test motion on simulators/idle robots first; robot status snapshots may lag and command delivery does not prove task execution.

## Migrating from 0.1.x

V3 tool names replace earlier smart-routing/legacy names: use `get_robot_status` rather than `get_robot_status_smart`, `list_task_reports` rather than `get_task_reports_smart`, `start_task` rather than `create_robot_command` for starting a defined task. Check the registry table for exact inputs (snake_case). To temporarily expose 0.1.x tools under `legacy_`-prefixed names set `GS_ENABLE_LEGACY_TOOLS=1`. OAuth lifetime handling now honors `expires_in`; remove any client workaround for premature/late refresh.

## Development

```sh
uv sync --extra dev
uv run pytest -q
uv run ruff check src tests
cd h5 && npm ci && npm run build
```

The H5 build writes `src/gs_openapi/server/static/`; build it before `uv build` so wheels contain the interface. Docker Compose reads `.env` from a local copy of `.env.example` (never commit `.env`).

## Links

[Docs](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/README.md) · [V3 API archive/index](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) · [Testing](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) · [Claude Code + Skill](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md) · [Changelog](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CHANGELOG.md) · [License](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)

## Disclaimer

Unofficial personal research software based on public Gausium OpenAPI V3 documentation; no Gausium affiliation, endorsement or support. Use at your own risk and validate robot commands on simulators/idle machines before operating live equipment.
