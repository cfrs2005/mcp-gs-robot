# 🤖 mcp-gs-robot

<div align="center">

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-gs-robot.svg)](https://pypi.org/project/mcp-gs-robot/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)
[![CI](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![OpenAPI V3](https://img.shields.io/badge/高仙_OpenAPI-V3-orange.svg)](https://developer.gs-robot.com/v3docs/zh_CN/OpenAPI%20V3/Overview)

**用自然语言指挥高仙清洁机器人 —— 在 Claude、Cursor、终端，或者手机上。**

*MCP 服务 · HTTP/REST 服务 · Pi Agent（CLI + H5）· Agent Skill —— 一套代码、一个工具注册表、基于高仙 OpenAPI V3。*

[快速开始](#-快速开始) · [MCP 工具](#-mcp-工具) · [Pi Agent](#-pi-agent) · [HTTP API 与 H5](#-http-api-与-h5) · [配置](#-配置) · [开发](#-开发) · [English](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md)

</div>

> ⚠️ **免责声明** —— 本项目是**非官方、个人研究学习用途的开源项目**，与高仙（Gausium）官方无任何隶属、认可或支持关系。使用风险自负。机器人指令会让实体机器移动，请先在模拟器或空闲机器人上测试。项目仅依据公开的[高仙 OpenAPI V3 文档](https://developer.gs-robot.com/v3docs/zh_CN/OpenAPI%20V3/Overview)实现。

---

## 🌟 这是什么？

`mcp-gs-robot` 把高仙 OpenAPI **V3**（机器人状态、地图、组合任务、排班、指令、报告）封装成带类型的 Python 客户端，并通过四个入口对外提供，四个入口共用**同一个工具注册表**：

| 入口 | 命令 | 适用场景 |
|---|---|---|
| 🔌 **MCP 服务**（stdio） | `mcp-gs-robot` | 让 Claude Code、Claude Desktop、Cursor、Cherry Studio 等 MCP 客户端直接操作机器人 |
| 🌐 **HTTP 服务**（FastAPI） | `gs-robot-server` | 需要 REST 接口、Swagger，以及内置的 **H5 移动端页面** |
| 🧠 **Pi Agent**（CLI + H5 对话） | `pi-agent` | 需要一个会规划、会执行、执行前会确认的机器人运维助手 |
| 📚 **Agent Skill** | `skills/gs-robot/` | 教 Claude Code / Codex / WorkBuddy 正确的操作流程 |

### ✨ 特性

- **40 个工具**：覆盖全部 36 个 V3 业务接口，外加工作流工具 `run_cleaning_task`、`wait_for_command`
- **类型化、有测试**：pydantic v2 模型、统一信封解包、六位业务错误码映射为 `GausiumAPIError`，48 个单测，无需联网
- **安全优先**：所有会让机器人动起来或改数据的工具都标记为 `dangerous`，在 Agent、CLI、H5 中都必须二次确认
- **OAuth 正确处理**：V3 的 `expires_in` 是毫秒时间戳而非秒数，token 管理器已正确解析并加锁刷新
- **严格对照官方文档**：每个接口都按[高仙 OpenAPI V3 官方文档](https://developer.gs-robot.com/v3docs/zh_CN/OpenAPI%20V3/Overview)实现，[`docs/apis.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) 把每个接口映射到对应官方页面
- **模型无关的 Agent**：默认 Anthropic（`claude-opus-5`），也支持任意 OpenAI 兼容端点（DeepSeek、本地模型……）

## 🏗️ 架构

![架构图](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/architecture.svg)

```
 Claude / Cursor / MCP 客户端       浏览器（H5）          终端
            │                          │                   │
   ┌────────▼────────┐        ┌────────▼────────┐  ┌───────▼───────┐
   │  MCP 服务        │        │  HTTP 服务       │  │  pi-agent CLI │
   │  gs_openapi.mcp │        │  REST + SSE     │  │               │
   └────────┬────────┘        └───┬─────────┬───┘  └───────┬───────┘
            │                     │         │              │
            │                     │   ┌─────▼──────────────▼─────┐
            │                     │   │  Pi Agent（工具循环、      │
            │                     │   │  确认门控、多 provider）   │
            │                     │   └─────────────┬─────────────┘
   ┌────────▼─────────────────────▼─────────────────▼─────────────┐
   │              工具注册表 gs_openapi.tools —— 40 个工具           │
   └──────────────────────────────┬────────────────────────────────┘
   ┌──────────────────────────────▼────────────────────────────────┐
   │   GausiumV3 客户端 · 模型 · 参考表 · token 管理器               │
   └──────────────────────────────┬────────────────────────────────┘
                                  ▼
                    https://openapi.gs-robot.com（OpenAPI V3）
```

完整契约（工具名、REST/SSE 协议、Agent 接口）见 [`docs/ARCHITECTURE_V3.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md)。

## 🚀 快速开始

### 1. 安装

```bash
pip install mcp-gs-robot          # 或：uv pip install mcp-gs-robot
```

源码安装：

```bash
git clone https://github.com/cfrs2005/mcp-gs-robot.git
cd mcp-gs-robot
uv sync                            # 创建 .venv 并安装全部运行依赖
```

### 2. 凭据

在[高仙开发者中心](https://developer.gs-robot.com/)创建应用和 AccessKey，然后：

```bash
export GS_CLIENT_ID="cli-xxxxxxxx"
export GS_CLIENT_SECRET="sk-xxxxxxxx"
export GS_OPEN_ACCESS_KEY="ak-xxxxxxxx"     # 填 AccessKeySecret，不是 AccessKeyID
```

工作目录下的 `.env` 也会被加载，模板见 [`.env.example`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/.env.example)。凭据不要提交到仓库。

### 3. 选一个入口

<details open>
<summary><b>🔌 MCP 服务 —— Claude Code / Claude Desktop / Cursor</b></summary>

```bash
# Claude Code 一行搞定
claude mcp add gs-robot \
  --env GS_CLIENT_ID="…" --env GS_CLIENT_SECRET="…" --env GS_OPEN_ACCESS_KEY="…" \
  -- mcp-gs-robot
```

或写入 `claude_desktop_config.json` / Cursor 的 MCP 配置：

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

然后直接问："列出我的机器人，显示电量和工作状态" → 自动调用 `list_robots` + `get_robot_status`。
传输方式为 **stdio**。设置 `GS_ENABLE_LEGACY_TOOLS=1` 可同时暴露 0.1.x 的旧工具（`legacy_*` 前缀）。

</details>

<details>
<summary><b>🌐 HTTP 服务 + H5 移动端</b></summary>

```bash
gs-robot-server                    # http://0.0.0.0:8000
```

- **H5 页面**：手机或浏览器打开 `http://localhost:8000/`
- **Swagger**：`http://localhost:8000/docs`
- **加保护**：设置 `GS_SERVER_API_KEY=…`，请求带 `X-API-Key`（H5 的"设置"页可填）

Docker：

```bash
cp .env.example .env && $EDITOR .env
docker compose up -d               # 构建 H5 + Python 镜像，监听 :8000
```

</details>

<details>
<summary><b>🧠 Pi Agent —— 在终端对话</b></summary>

```bash
export ANTHROPIC_API_KEY="…"                 # 默认 provider：Anthropic，模型 claude-opus-5
pi-agent --robot GS438-0120-X8P-0001

# 或任意 OpenAI 兼容端点（DeepSeek、vLLM、Ollama……）
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
<summary><b>📚 Agent Skill —— Claude Code / Codex / WorkBuddy</b></summary>

```bash
# Claude Code（用户级）
cp -r skills/gs-robot ~/.claude/skills/gs-robot
# Codex CLI
cp -r skills/gs-robot ~/.codex/skills/gs-robot
```

Skill 内置了安全操作流程（状态 → 能力 → 资源 → 任务定义 → 启动 → 轮询），并附带工作状态、指令类型、任务启动错误码等参考表。详见 [`skills/gs-robot/README.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md)。

</details>

## 🧰 MCP 工具

40 个工具在 `gs_openapi/tools/` 中只定义一次，MCP、Agent、REST（`POST /api/v1/tools/{name}`）拿到的完全一致。输入参数为 `snake_case`，注册表内部映射为 V3 的 `camelCase` 字段。**⚠️ = 危险工具**（会让机器人移动或修改数据，Agent 执行前会要求确认）。

<details open>
<summary><b>机器人与地图</b></summary>

| 工具 | 必填参数 | 可选 | 说明 |
|---|---|---|---|
| `list_robots` | – | `page`、`page_size`、`relation` | 走旧版 `v1alpha1/robots`（V3 无列表接口） |
| `get_robot_status` | `robot_sn_list`（≤100） | | 附加 `work_state_name` / `work_state_desc`；快照延迟 ≤30 s |
| `describe_work_state` | `work_state` | | 本地查表，不调 API |
| `get_robot_capabilities` | `robot_sn` | | 是否支持组合任务 / 定时排班 |
| `list_robot_maps` | `robot_sn` | | `mapId`、`mapVersionId`、`displayName` |
| `get_map_canvas` | `robot_sn`、`map_id` | | 临时 PNG 地址 + 栅格元数据 |
| `list_charging_positions` | `robot_sn`、`map_id` | | |
| `list_map_resources` | `robot_sn`、`map_id_list` | `include_paths/regions/positions` | 不含工作模式的地图资源 |
| `list_task_resources` | `robot_sn`、`map_id_list` | `include_paths/regions/positions` | **建任务/排班前必查** |

</details>

<details>
<summary><b>任务（组合任务）</b></summary>

| 工具 | 必填参数 | 可选 | |
|---|---|---|---|
| `list_work_modes` | `robot_sn` | | |
| `list_task_definitions` | `robot_sn` | `page`、`pagesize`、`site_id`、`task_name` | |
| `get_task_definition` | `robot_sn`、`fusion_task_id` | | |
| `create_task_definition` | `robot_sn`、`task_name`、`work_mode`、`map_resource_list` | `loop_count`、`site_id`、`task_advance_config` | ⚠️ |
| `update_task_definition` | `robot_sn`、`fusion_task_id` | 同创建 | ⚠️ |
| `delete_task_definition` | `robot_sn`、`fusion_task_id` | | ⚠️ |
| `start_task` | `robot_sn`、`fusion_task_id` | `loop_count` | ⚠️ 返回 `requestId`、`taskInstanceId` |
| `pause_task` / `resume_task` / `stop_task` / `skip_task_item` | `robot_sn` | | ⚠️ |

</details>

<details>
<summary><b>排班</b></summary>

| 工具 | 必填参数 | |
|---|---|---|
| `create_simple_schedule` | `robot_sn`、`task_name`、`site_mode`、`work_mode`、`map_resource_list`、`plan_execute_type`、`plan_repeat_type`、`plan_start_date`、`plan_start_time` | ⚠️ |
| `update_simple_schedule` / `delete_simple_schedule` | `robot_sn`、`plan_uuid`、`year`、`month`、`day_of_month`、`operation_type` | ⚠️ |
| `create_schedule` / `update_schedule` / `delete_schedule` | 标准排班字段（见[文档归档](https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Overview)） | ⚠️ |
| `list_schedules` | `robot_sn` | |
| `get_schedule` | `robot_sn`、`plan_uuid`、`year`、`month`、`day_of_month` | |
| `get_schedule_calendar` | `robot_sn`、`year_month` | |
| `list_schedule_pre_tasks` | `robot_sn`、`date` | |

</details>

<details>
<summary><b>指令、报告与工作流</b></summary>

| 工具 | 必填参数 | 可选 | |
|---|---|---|---|
| `get_command_status` | `robot_sn`、`request_id` | | `cmdStatus=6` 表示已下发，**不代表**执行完成 |
| `list_command_history` | `robot_sn` | `page`、`pagesize`、`cmd_status`、`command_type` | |
| `navigate_home` | `robot_sn`、`map_id` | `map_resource_id` | ⚠️ |
| `pause_navigation` / `resume_navigation` / `stop_navigation` | `robot_sn` | | ⚠️ |
| `list_task_reports` | `robot_sn` | `page`、`pagesize`、`end_time_min`、`end_time_max` | |
| `get_task_report_map_images` | `task_report_id` | `robot_sn` | |
| `wait_for_command` | `robot_sn`、`request_id` | `timeout_seconds` | 轮询直到 `cmdStatus` 终态 |
| `run_cleaning_task` | `robot_sn`、`task_name`、`map_id`、`resource_ids` | `mode`、`strength`、`loop_count`、`wait_seconds` | ⚠️ 能力 → 资源 → 建任务 → 启动 → 轮询 |

</details>

随时可以从代码重新生成这份清单：

```bash
uv run python -c "from gs_openapi.tools.registry import REGISTRY; [print(t.category, t.name, '⚠️' if t.dangerous else '') for t in REGISTRY.values()]"
```

## 🧠 Pi Agent

Pi Agent 是一个小而完整、与模型无关的工具调用循环（`gs_openapi/agent/`），同样建立在工具注册表之上：

- **Provider**：`anthropic`（官方 SDK，流式输出、adaptive thinking、提示缓存）或 `openai`（任何 OpenAI 兼容的 `/chat/completions`）
- **确认门控**：危险工具会先发出 `confirm_required` 并等待批准 —— CLI 里是 `[y/N]`，H5 里是按钮，REST 里是 `POST …/confirm`。`PI_AGENT_AUTO_APPROVE=1` 可关闭（不推荐）
- **有边界**：`PI_AGENT_MAX_TURNS`（默认 12）限制工具循环次数；工具结果超过 2 万字符会截断
- **同一个大脑**：CLI、H5 对话、`POST /api/v1/agent/...` 跑的都是 `PiAgent.run()`

## 🌐 HTTP API 与 H5

统一前缀 `/api/v1`。`GET /api/v1/health` 公开；设置了 `GS_SERVER_API_KEY` 后其余接口都需要 `X-API-Key`。错误统一为 `{"error": {"code", "message", "trace_id"}}`（上游 V3 错误 → HTTP 502，`code` 为六位业务码）。

| 领域 | 路由 |
|---|---|
| 工具 | `POST /tools/{tool_name}` —— 用工具的 JSON 输入直接调用任意注册表工具 |
| 机器人 | `GET /robots` · `POST /robots/status` · `GET /robots/{sn}/status` · `/capabilities` · `/work-modes` |
| 地图 | `GET /robots/{sn}/maps` · `/maps/{map_id}/canvas` · `/maps/{map_id}/resources` |
| 任务 | `GET/POST /robots/{sn}/task-definitions` · `GET/PUT/DELETE …/{fusion_task_id}` · `POST /robots/{sn}/tasks/{start\|pause\|resume\|stop\|skip}` |
| 导航 | `POST /robots/{sn}/navigation/{go-home\|pause\|resume\|stop}` |
| 指令与报告 | `GET /robots/{sn}/commands` · `…/commands/{request_id}` · `GET /robots/{sn}/reports` |
| 排班 | `GET/POST /robots/{sn}/schedules` · `POST …/schedules/simple` · `GET/PUT/DELETE …/schedules/{plan_id}` |
| Agent | `POST /agent/sessions` · `GET/DELETE /agent/sessions/{id}` · `POST …/{id}/messages`（**SSE**）· `POST …/{id}/confirm` |

`/messages` 的 SSE 事件：`text_delta` · `tool_call` · `tool_result` · `confirm_required` · `done` · `error`。

```bash
SID=$(curl -s -XPOST -H "X-API-Key: $KEY" localhost:8000/api/v1/agent/sessions | jq -r .session_id)
curl -N -XPOST -H "X-API-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"content":"列出我的机器人和电量"}' \
  localhost:8000/api/v1/agent/sessions/$SID/messages
```

**H5**（`h5/`，Vue 3 + Vite + Vant）：对话（流式输出、工具卡片、确认按钮）· 机器人（在线/电量/工作状态列表）· 详情（地图与画布、任务定义、快捷操作、报告）· 设置（API 地址 / Key）。生产构建产物已提交到 `src/gs_openapi/server/static/`，`pip install` 即自带。

## 🔧 配置

| 变量 | 默认值 | 说明 |
|---|---|---|
| `GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` | – | **必填。** 高仙应用 + AccessKey 凭据 |
| `GS_BASE_URL` | `https://openapi.gs-robot.com/` | 上游地址（测试时可指向 mock） |
| `GS_HTTP_TIMEOUT` | `30` | HTTP 超时（秒） |
| `GS_ENABLE_LEGACY_TOOLS` | 未设置 | `1` 时 MCP 服务额外注册 0.1.x 旧工具（`legacy_*`） |
| `GS_SERVER_HOST` / `GS_SERVER_PORT` | `0.0.0.0` / `8000` | HTTP 服务监听地址 |
| `GS_SERVER_API_KEY` | 未设置 | 设置后受保护接口需要 `X-API-Key` |
| `PI_AGENT_PROVIDER` | `anthropic` | `anthropic` 或 `openai` |
| `PI_AGENT_MODEL` | `claude-opus-5` / `deepseek-chat` | 各 provider 的模型 ID |
| `ANTHROPIC_API_KEY` | – | Anthropic provider 密钥 |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | – | OpenAI 兼容 provider |
| `PI_AGENT_AUTO_APPROVE` | `0` | `1` 跳过危险工具确认 |
| `PI_AGENT_MAX_TURNS` | `12` | 每条用户消息的最大工具循环次数 |

## 📂 项目结构

```
src/gs_openapi/
├── auth/token_manager.py      OAuth token（毫秒时间戳过期、加锁刷新）
├── core/                      HTTP 客户端、V3 端点注册、错误类型
├── v3/                        GausiumV3 门面 · pydantic 模型 · 参考表
├── tools/                     工具注册表（MCP / Agent / REST 的单一真源）
├── mcp/                       FastMCP 服务（v3_server.py）+ legacy_tools.py
├── agent/                     Pi Agent 核心、provider、会话存储、CLI
├── server/                    FastAPI 应用、路由、SSE、H5 静态托管
└── main.py                    `mcp-gs-robot` stdio 入口
h5/                            Vue 3 移动端页面（构建到 server/static）
skills/gs-robot/               Agent Skill 与参考资料
docs/ARCHITECTURE_V3.md        所有模块遵守的契约
tests/                         48 个单测（httpx.MockTransport，无需联网）
```

## 🧑‍💻 开发

```bash
uv sync --extra dev
uv run pytest -q                 # 48 passed
uv run ruff check src tests
cd h5 && npm ci && npm run build # 重新构建 H5 到 src/gs_openapi/server/static
uv build                         # wheel 中包含 H5 静态资源
```

新增一个 V3 工具：在 `src/gs_openapi/tools/v3_tools.py` 用 `@tool(...)` 装饰器定义输入模型和处理函数，MCP、REST、Agent 会自动识别；再补上表格行和测试。规范见 [`CLAUDE.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CLAUDE.md)，curl 演练和 MCP Inspector 用法见[测试指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md)。

## 🔁 从 0.1.x 迁移

| 0.1.x | 0.2.0 |
|---|---|
| `get_robot_status_smart`、`get_robot_status`（按 SN 前缀路由 v1/v2） | `get_robot_status`（V3 快照，不分系列，批量 ≤100） |
| `get_task_reports_smart`、`list_robot_task_reports` | `list_task_reports` |
| `create_robot_command`（start/pause/stop） | `start_task` / `pause_task` / `resume_task` / `stop_task`、`navigate_home` |
| `submit_temp_site_task`、`execute_*_workflow` | `create_task_definition` + `start_task`，或 `run_cleaning_task` |
| `list_robot_maps`（openapi/v1） | `list_robot_maps`（V3）+ `list_task_resources` |

旧工具在 `GS_ENABLE_LEGACY_TOOLS=1` 时仍以 `legacy_*` 名称可用。OAuth `expires_in` 的老 bug（把毫秒时间戳当秒数）已修复，可移除相关的刷新绕过逻辑。

## 📖 文档

| 文档 | 用途 |
|---|---|
| [架构契约](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md) | 工具名、REST/SSE 协议、Agent 接口 |
| [V3 接口索引](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) | 每个接口的方法、路径、支持的固件版本及官方页面链接 |
| [Claude Code 集成](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md) | MCP 配置 + Skill |
| [测试指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) | 单测、curl 演练、MCP Inspector |
| [Skill 说明](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md) | 在 Claude Code / Codex / WorkBuddy 中安装 Skill |
| [更新日志](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CHANGELOG.md) | 版本变更 |

## 🤝 参与贡献

1. Fork 并创建功能分支
2. `uv sync --extra dev`，完成修改并补充测试
3. `uv run pytest -q && uv run ruff check src tests`
4. 改动了注册表就同步更新文档和工具表
5. 提交 Pull Request

## 📄 许可证

MIT —— 见 [LICENSE](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)。

## ⚠️ 免责声明

本项目是**非官方、个人研究学习用途的开源项目**，仅依据高仙公开的 OpenAPI V3 文档实现，与高仙官方无任何隶属、认可或支持关系。不提供任何形式的担保；你对自己下发给机器人的每一条指令负责。请务必先在模拟器或空闲机器上验证，凭据不要进入版本控制，并牢记"命令已下发（`cmdStatus=6`）"不等于"任务已完成"。

---

<div align="center">

*献给那些宁愿跟机器人说话、也不想在控制台里点来点去的人。* 🤖✨

</div>
