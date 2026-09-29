<div align="center">

# 🤖 mcp-gs-robot

**用自然语言指挥高仙清洁机器人 —— 在 Claude、Cursor、终端，或者手机上。**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-gs-robot.svg)](https://pypi.org/project/mcp-gs-robot/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)
[![CI](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![OpenAPI V3](https://img.shields.io/badge/高仙_OpenAPI-V3-orange.svg)](https://developer.gs-robot.com/v3docs/zh_CN/OpenAPI%20V3/Overview)

MCP 服务 · HTTP/REST 服务 · Pi Agent（CLI + H5）· Agent Skill<br>
一套代码、一个工具注册表，基于高仙 OpenAPI V3

[快速开始](#-快速开始) · [安全机制](#-安全机制) · [工具](#-工具) · [HTTP API 与 H5](#-http-api-与-h5) · [配置](#-配置) · [开发](#-开发) · [English](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md)

</div>

> ⚠️ **免责声明** —— 本项目是**非官方、个人研究学习用途的开源项目**，与高仙（Gausium）官方无任何隶属、认可或支持关系，使用风险自负。机器人指令会让实体机器移动，请先在模拟器或空闲机器人上测试。项目仅依据公开的[高仙 OpenAPI V3 文档](https://developer.gs-robot.com/v3docs/zh_CN/OpenAPI%20V3/Overview)实现。

![H5 页面：Pi Agent 对话、机器人列表、地图与报告](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/h5-showcase_cn.png)

<sub>内置 H5 页面截图，连接 mock 上游，数据为演示数据。</sub>

## 🌟 这是什么？

`mcp-gs-robot` 把高仙 OpenAPI **V3**（机器人状态、地图、组合任务、排班、指令、报告）封装成带类型的 Python 客户端，并通过四个入口对外提供，四个入口共用**同一个工具注册表**：

| | 入口 | 命令 | 适用场景 |
|---|---|---|---|
| 🔌 | **MCP 服务**（stdio） | `mcp-gs-robot` | 让 Claude Code、Claude Desktop、Cursor、Cherry Studio 等 MCP 客户端直接操作机器人 |
| 🌐 | **HTTP 服务**（FastAPI） | `gs-robot-server` | 需要 REST 接口、Swagger，以及内置的 **H5 移动端页面** |
| 🧠 | **Pi Agent**（CLI + H5 对话） | `pi-agent` | 需要一个会规划、会执行、执行前会确认的机器人运维助手 |
| 📚 | **Agent Skill** | `skills/gs-robot/` | 教 Claude Code / Codex / WorkBuddy 正确的操作流程 |

![架构图](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/architecture_cn.svg)

- **40 个工具**：覆盖全部 36 个 V3 业务接口，外加工作流工具 `run_cleaning_task`、`wait_for_command`
- **类型化、有测试**：pydantic v2 模型、统一信封解包、六位业务错误码映射为 `GausiumAPIError`；50 个离线测试
- **安全优先**：所有会让机器人动起来或改数据的工具都标记为 `dangerous`，在 Agent、CLI、H5 中都必须明确确认
- **OAuth 正确处理**：V3 的 `expires_in` 是毫秒时间戳而非秒数，token 管理器已正确解析并加锁刷新
- **模型无关的 Agent**：默认 Anthropic（`claude-opus-5`），也支持任意 OpenAI 兼容端点（DeepSeek、vLLM、Ollama……）
- **严格对照官方文档**：[`docs/apis.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) 把每个接口映射到对应官方页面；完整契约见 [`docs/ARCHITECTURE_V3.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md)

## 🚀 快速开始

**1 · 安装**

```bash
pip install mcp-gs-robot            # 或：uv pip install mcp-gs-robot
# 从源码安装
git clone https://github.com/cfrs2005/mcp-gs-robot.git && cd mcp-gs-robot && uv sync
```

**2 · 凭据**：在[高仙开发者中心](https://developer.gs-robot.com/)创建应用和 AccessKey：

```bash
export GS_CLIENT_ID="cli-xxxxxxxx"
export GS_CLIENT_SECRET="sk-xxxxxxxx"
export GS_OPEN_ACCESS_KEY="ak-xxxxxxxx"     # 填 AccessKeySecret，不是 AccessKeyID
```

也会读取当前目录下的 `.env`（参考 [`.env.example`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/.env.example)）。不要把凭据提交到仓库。

**3 · 选一个入口**

<details open>
<summary><b>🔌 MCP 服务 —— Claude Code / Claude Desktop / Cursor</b></summary>

```bash
claude mcp add gs-robot \
  --env GS_CLIENT_ID="…" --env GS_CLIENT_SECRET="…" --env GS_OPEN_ACCESS_KEY="…" \
  -- mcp-gs-robot
```

或者写进 `claude_desktop_config.json` / Cursor 的 MCP 设置：

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

然后直接问：*「列出我的机器人，显示电量和工作状态」* → `list_robots` + `get_robot_status`。
传输方式为 **stdio**。设置 `GS_ENABLE_LEGACY_TOOLS=1` 会额外以 `legacy_*` 名称暴露 0.1.x 的旧工具。

</details>

<details>
<summary><b>🌐 HTTP 服务 + H5 移动端</b></summary>

```bash
gs-robot-server                     # http://0.0.0.0:8000
```

- **H5 页面**：用手机或浏览器打开 `http://localhost:8000/`
- **Swagger**：`http://localhost:8000/docs`
- **加保护**：设置 `GS_SERVER_API_KEY=…`，请求时带 `X-API-Key`（H5 的「设置」页可以保存）

```bash
cp .env.example .env && $EDITOR .env
docker compose up -d                # 构建 H5 + Python 镜像，监听 :8000
```

</details>

<details>
<summary><b>🧠 Pi Agent —— 在终端里对话</b></summary>

```bash
export ANTHROPIC_API_KEY="…"                 # 默认 provider：Anthropic，模型 claude-opus-5
pi-agent --robot GS438-0120-X8P-0001

# 或任意 OpenAI 兼容端点
PI_AGENT_PROVIDER=openai OPENAI_BASE_URL=https://api.deepseek.com/v1 OPENAI_API_KEY=… \
PI_AGENT_MODEL=deepseek-chat pi-agent
```

```
› 一楼大厅的机器人现在什么状态？电量够不够跑一次清扫？
⚙ get_robot_status(robot_sn_list=["GS438-0120-X8P-0001"])
机器人在线，电量 82%，状态 IDLE（空闲），当前地图「一楼大厅」，可以执行任务。
› 好，启动「大厅每日尘推」
⚙ list_task_definitions(...)
⚠ 即将执行危险操作 start_task robot_sn=GS438-… fusion_task_id=… 确认？[y/N] y
⚙ start_task(...)  ⚙ wait_for_command(...)
命令已下发（cmdStatus=6），任务实例 47d029ee… 已开始。
```

</details>

<details>
<summary><b>📚 Agent Skill —— Claude Code / Codex / WorkBuddy</b></summary>

```bash
cp -r skills/gs-robot ~/.claude/skills/gs-robot     # Claude Code（用户级）
cp -r skills/gs-robot ~/.codex/skills/gs-robot      # Codex CLI
```

Skill 固化了安全操作流程（状态 → 能力 → 资源 → 任务定义 → 启动 → 轮询），并附带工作状态、指令类型、任务启动错误码的参考表。详见 [`skills/gs-robot/README.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md)。

</details>

## 🔒 安全机制

会让机器人移动或修改数据的工具注册时都带 `dangerous=True`。Pi Agent 不会自行执行它们，而是先发出 `confirm_required` 并等待：终端里是 `[y/N]`，H5 里是按钮，REST 则是 `POST …/confirm`。被拒绝的调用永远不会触达机器人。

![危险工具确认流程](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/confirm-flow_cn.svg)

有两点需要注意：

- **已下发不等于已完成。** `cmdStatus=6` 只表示机器人收到了指令，之后请用 `get_robot_status` 或任务报告跟进。
- **REST 直接执行。** `POST /api/v1/tools/{name}` 视调用方已经确认过，请在你自己的客户端里做确认。`PI_AGENT_AUTO_APPROVE=1` 会关闭 Agent 的确认闸门（不推荐）。

最常见的「清扫这几个区域」场景，可以用 `run_cleaning_task` 把整个流程打包成一次确认调用：

![run_cleaning_task 工作流](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/cleaning-workflow_cn.svg)

## 🧰 工具

全部 40 个工具只在 `gs_openapi/tools/` 中定义一次，以完全相同的方式暴露给 MCP、Agent 和 REST（`POST /api/v1/tools/{name}`）。输入统一为 `snake_case`，由注册表映射成 V3 的 `camelCase`。**⚠️ = 危险工具。**

| 分类 | 工具 |
|---|---|
| **机器人** | `list_robots` · `get_robot_status` · `describe_work_state` · `get_robot_capabilities` |
| **地图** | `list_robot_maps` · `get_map_canvas` · `list_charging_positions` · `list_map_resources` · `list_task_resources` |
| **任务** | `list_work_modes` · `list_task_definitions` · `get_task_definition` · `create_task_definition` ⚠️ · `update_task_definition` ⚠️ · `delete_task_definition` ⚠️ · `start_task` ⚠️ · `pause_task` ⚠️ · `resume_task` ⚠️ · `stop_task` ⚠️ · `skip_task_item` ⚠️ |
| **定时排班** | `list_schedules` · `get_schedule` · `get_schedule_calendar` · `list_schedule_pre_tasks` · `create_simple_schedule` ⚠️ · `update_simple_schedule` ⚠️ · `delete_simple_schedule` ⚠️ · `create_schedule` ⚠️ · `update_schedule` ⚠️ · `delete_schedule` ⚠️ |
| **指令** | `get_command_status` · `list_command_history` · `navigate_home` ⚠️ · `pause_navigation` ⚠️ · `resume_navigation` ⚠️ · `stop_navigation` ⚠️ |
| **报告** | `list_task_reports` · `get_task_report_map_images` |
| **工作流** | `wait_for_command` · `run_cleaning_task` ⚠️ |

<details>
<summary><b>各工具的输入参数</b></summary>

**机器人与地图**

| 工具 | 必填 | 可选 | 说明 |
|---|---|---|---|
| `list_robots` | – | `page`、`page_size`、`relation` | 走 legacy `v1alpha1/robots`（V3 没有列表接口） |
| `get_robot_status` | `robot_sn_list`（≤100） | | 附加 `work_state_name` / `work_state_desc`；快照最多延迟 30 秒 |
| `describe_work_state` | `work_state` | | 本地查表，不调接口 |
| `get_robot_capabilities` | `robot_sn` | | 是否支持组合任务 / 定时任务 |
| `list_robot_maps` | `robot_sn` | | `mapId`、`mapVersionId`、`displayName` |
| `get_map_canvas` | `robot_sn`、`map_id` | | 临时 PNG 地址 + 栅格元数据 |
| `list_charging_positions` | `robot_sn`、`map_id` | | |
| `list_map_resources` | `robot_sn`、`map_id_list` | `include_paths/regions/positions` | 不含工作模式的地图资源 |
| `list_task_resources` | `robot_sn`、`map_id_list` | `include_paths/regions/positions` | **创建任务 / 排班前先查它** |

**任务（组合任务）**

| 工具 | 必填 | 可选 | |
|---|---|---|---|
| `list_work_modes` | `robot_sn` | | |
| `list_task_definitions` | `robot_sn` | `page`、`pagesize`、`site_id`、`task_name` | |
| `get_task_definition` | `robot_sn`、`fusion_task_id` | | |
| `create_task_definition` | `robot_sn`、`task_name`、`work_mode`、`map_resource_list` | `loop_count`、`site_id`、`task_advance_config` | ⚠️ |
| `update_task_definition` | `robot_sn`、`fusion_task_id` | 同创建 | ⚠️ |
| `delete_task_definition` | `robot_sn`、`fusion_task_id` | | ⚠️ |
| `start_task` | `robot_sn`、`fusion_task_id` | `loop_count` | ⚠️ 返回 `requestId`、`taskInstanceId` |
| `pause_task` / `resume_task` / `stop_task` / `skip_task_item` | `robot_sn` | | ⚠️ |

**定时排班**

| 工具 | 必填 | |
|---|---|---|
| `create_simple_schedule` | `robot_sn`、`task_name`、`site_mode`、`work_mode`、`map_resource_list`、`plan_execute_type`、`plan_repeat_type`、`plan_start_date`、`plan_start_time` | ⚠️ |
| `update_simple_schedule` / `delete_simple_schedule` | `robot_sn`、`plan_uuid`、`year`、`month`、`day_of_month`、`operation_type` | ⚠️ |
| `create_schedule` / `update_schedule` / `delete_schedule` | 标准排班字段（见[官方文档](https://developer.gs-robot.com/v3docs/zh_CN/OpenAPI%20V3/Overview)） | ⚠️ |
| `list_schedules` | `robot_sn` | |
| `get_schedule` | `robot_sn`、`plan_uuid`、`year`、`month`、`day_of_month` | |
| `get_schedule_calendar` | `robot_sn`、`year_month` | |
| `list_schedule_pre_tasks` | `robot_sn`、`date` | |

**指令、报告与工作流**

| 工具 | 必填 | 可选 | |
|---|---|---|---|
| `get_command_status` | `robot_sn`、`request_id` | | `cmdStatus=6` 表示已下发，**不是**已完成 |
| `list_command_history` | `robot_sn` | `page`、`pagesize`、`cmd_status`、`command_type` | |
| `navigate_home` | `robot_sn`、`map_id` | `map_resource_id` | ⚠️ |
| `pause_navigation` / `resume_navigation` / `stop_navigation` | `robot_sn` | | ⚠️ |
| `list_task_reports` | `robot_sn` | `page`、`pagesize`、`end_time_min`、`end_time_max` | |
| `get_task_report_map_images` | `task_report_id` | `robot_sn` | |
| `wait_for_command` | `robot_sn`、`request_id` | `timeout_seconds` | 轮询直到 `cmdStatus` 进入终态 |
| `run_cleaning_task` | `robot_sn`、`task_name`、`map_id`、`resource_ids` | `mode`、`strength`、`loop_count`、`wait_seconds` | ⚠️ 能力 → 资源 → 创建 → 启动 → 轮询 |

</details>

从注册表重新生成工具清单：

```bash
uv run python -c "from gs_openapi.tools.registry import REGISTRY; [print(t.category, t.name, '⚠️' if t.dangerous else '') for t in REGISTRY.values()]"
```

## 🌐 HTTP API 与 H5

统一前缀 `/api/v1`。`GET /api/v1/health` 无需鉴权；设置了 `GS_SERVER_API_KEY` 时，其余接口都要带 `X-API-Key`。错误统一使用 `{"error": {"code", "message", "trace_id"}}` 信封；上游 V3 错误映射为 HTTP 502，并携带六位业务码。

| 分类 | 路由 |
|---|---|
| 工具 | `POST /tools/{tool_name}` —— 用工具的 JSON 输入调用任意注册表工具 |
| 机器人 | `GET /robots` · `POST /robots/status` · `GET /robots/{sn}/status` · `/capabilities` · `/work-modes` |
| 地图 | `GET /robots/{sn}/maps` · `/maps/{map_id}/canvas` · `/maps/{map_id}/resources` |
| 任务 | `GET/POST /robots/{sn}/task-definitions` · `GET/PUT/DELETE …/{fusion_task_id}` · `POST /robots/{sn}/tasks/{start\|pause\|resume\|stop\|skip}` |
| 导航 | `POST /robots/{sn}/navigation/{go-home\|pause\|resume\|stop}` |
| 指令与报告 | `GET /robots/{sn}/commands` · `…/commands/{request_id}` · `GET /robots/{sn}/reports` |
| 定时排班 | `GET/POST /robots/{sn}/schedules` · `POST …/schedules/simple` · `GET/PUT/DELETE …/schedules/{plan_id}` |
| Agent | `POST /agent/sessions` · `GET/DELETE /agent/sessions/{id}` · `POST …/{id}/messages`（**SSE**）· `POST …/{id}/confirm` |

`/messages` 的 SSE 事件：`text_delta` · `tool_call` · `tool_result` · `confirm_required` · `done` · `error`。

```bash
SID=$(curl -s -XPOST -H "X-API-Key: $KEY" localhost:8000/api/v1/agent/sessions | jq -r .session_id)
curl -N -XPOST -H "X-API-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"content":"列出我的机器人和电量"}' \
  localhost:8000/api/v1/agent/sessions/$SID/messages
```

**H5**（`h5/`，Vue 3 + Vite + Vant）有四个页面：**对话**（流式对话，带工具卡片和确认按钮）、**机器人**（机器人列表，显示在线状态、电量、工作状态）、**详情**（地图与画布、任务定义、快捷操作、报告）、**设置**（API 地址与密钥）。生产构建产物已提交到 `src/gs_openapi/server/static/`，`pip install` 即自带 H5。

## 🔧 配置

| 变量 | 默认值 | 说明 |
|---|---|---|
| `GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` | – | **必填。** 高仙应用与 AccessKey 凭据 |
| `GS_BASE_URL` | `https://openapi.gs-robot.com/` | 上游地址（测试时可指向 mock） |
| `GS_HTTP_TIMEOUT` | `30` | HTTP 超时（秒） |
| `GS_ENABLE_LEGACY_TOOLS` | 未设置 | 设为 `1` 时 MCP 服务额外注册 `legacy_*` 旧工具 |
| `GS_SERVER_HOST` / `GS_SERVER_PORT` | `0.0.0.0` / `8000` | HTTP 服务监听地址 |
| `GS_SERVER_API_KEY` | 未设置 | 设置后，受保护路由要求 `X-API-Key` |
| `PI_AGENT_PROVIDER` | `anthropic` | `anthropic` 或 `openai` |
| `PI_AGENT_MODEL` | `claude-opus-5` / `deepseek-chat` | 各 provider 的模型 ID |
| `ANTHROPIC_API_KEY` | – | Anthropic provider 密钥 |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | – | OpenAI 兼容 provider |
| `PI_AGENT_AUTO_APPROVE` | `0` | 设为 `1` 时跳过危险工具确认 |
| `PI_AGENT_MAX_TURNS` | `12` | 每条用户消息最多的工具循环次数（工具结果超过 2 万字符会截断） |

## 🧑‍💻 开发

```
src/gs_openapi/
├── auth/token_manager.py      OAuth token（毫秒时间戳过期、加锁刷新）
├── core/                      HTTP 客户端、V3 接口注册表、错误类型
├── v3/                        GausiumV3 门面 · pydantic 模型 · 参考表
├── tools/                     工具注册表（MCP / Agent / REST 的唯一真源）
├── mcp/                       FastMCP 服务（v3_server.py）+ legacy_tools.py
├── agent/                     Pi Agent 核心、provider、会话存储、CLI
├── server/                    FastAPI 应用、路由、SSE、H5 静态托管
└── main.py                    `mcp-gs-robot` stdio 入口
h5/                            Vue 3 移动端（构建到 server/static）
skills/gs-robot/               Agent Skill 及参考资料
docs/ARCHITECTURE_V3.md        所有模块遵循的契约
tests/                         离线测试（httpx.MockTransport，无需联网）
```

```bash
uv sync --extra dev
uv run pytest -q                    # 50 passed
uv run ruff check src tests
cd h5 && npm ci && npm run build    # 重新构建 H5 到 src/gs_openapi/server/static
uv build                            # wheel 包含 H5 静态资源
```

新增 V3 工具：在 `src/gs_openapi/tools/v3_tools.py` 用 `@tool(...)` 定义输入模型和处理函数，MCP、REST、Agent 会自动接入；再补一个测试，并更新上面的工具表。开发约定见 [`CLAUDE.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CLAUDE.md)，curl 演练与 MCP Inspector 用法见[测试指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md)。

<details>
<summary><b>🔁 从 0.1.x 迁移</b></summary>

| 0.1.x | 0.2.0 |
|---|---|
| `get_robot_status_smart`、`get_robot_status`（按 SN 前缀路由 v1/v2） | `get_robot_status`（V3 快照，全系列，批量 ≤100） |
| `get_task_reports_smart`、`list_robot_task_reports` | `list_task_reports` |
| `create_robot_command`（启动 / 暂停 / 停止） | `start_task` / `pause_task` / `resume_task` / `stop_task`、`navigate_home` |
| `submit_temp_site_task`、`execute_*_workflow` | `create_task_definition` + `start_task`，或 `run_cleaning_task` |
| `list_robot_maps`（openapi/v1） | `list_robot_maps`（V3）+ `list_task_resources` |

设置 `GS_ENABLE_LEGACY_TOOLS=1` 后，旧工具仍以 `legacy_*` 名称可用。OAuth `expires_in` 的 bug（把毫秒时间戳当成秒数）已修复，可以删掉之前为刷新 token 做的临时处理。

</details>

## 📖 文档

| 文档 | 用途 |
|---|---|
| [架构契约](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md) | 工具名、REST/SSE 协议、Agent 接口 |
| [V3 接口索引](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) | 每个接口的方法、路径、支持固件及官方文档链接 |
| [Claude Code 集成](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md) | MCP 配置 + Skill |
| [测试指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) | 单元测试、curl 演练、MCP Inspector |
| [Skill 说明](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md) | 在 Claude Code / Codex / WorkBuddy 中安装 Skill |
| [更新日志](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CHANGELOG.md) | 版本发布说明 |

## 🤝 参与贡献

Fork 仓库并新建分支，执行 `uv sync --extra dev`，改动时附带测试，运行 `uv run pytest -q && uv run ruff check src tests`；如果改了注册表请同步更新工具表，然后提交 Pull Request。

## 📄 许可证

MIT，见 [LICENSE](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)。

## ⚠️ 免责声明

本项目是**非官方、个人研究学习用途的开源项目**，仅依据高仙公开的 OpenAPI V3 文档实现，与高仙（Gausium）官方无任何隶属、认可或支持关系。不提供任何形式的担保，你需要对自己下发指令的机器人负责。请务必先在模拟器或空闲机器人上验证，不要把凭据提交到版本库，并记住：指令已下发（`cmdStatus=6`）不代表任务已完成。

<div align="center">

*献给宁愿直接问机器人、也不想在控制台里点来点去的人。* 🤖✨

</div>
