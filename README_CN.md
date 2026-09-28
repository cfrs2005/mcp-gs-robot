# mcp-gs-robot · OpenAPI V3

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/) [![PyPI](https://img.shields.io/pypi/v/mcp-gs-robot)](https://pypi.org/project/mcp-gs-robot/) [![MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE) [![CI](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml) · [English](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md)

> ⚠️ **免责声明**：本项目为非官方、个人研究学习用途的开源项目，与高仙（Gausium）官方无任何隶属、认可或支持关系。使用风险自负。机器人指令可能导致实体机器移动，请先在模拟器或空闲机器人上测试。本项目依托公开的高仙 OpenAPI V3 文档。

## 项目简介

一个仓库提供四个入口：MCP stdio 服务、Pi Agent 命令行（Anthropic 或 OpenAI 兼容模型）、FastAPI REST/SSE 服务及 H5 页面、可复用 Agent Skill。四者共用 V3 工具注册表；`list_robots` 因 V3 不提供列表接口而使用旧版 v1alpha1。安装包已包含服务器和 Agent 的运行依赖，无需另装 extra。

## 架构

![四种入口共享 V3 工具注册表](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/images/architecture.svg)

注册表将 snake_case 工具输入映射至 V3 客户端、HTTP 客户端和 token 管理器。参见[架构契约](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md)。

## 快速开始

需要 Python 3.12+ 与自行申请的 OpenAPI 凭据。通过环境变量传入，不要提交到仓库：

```sh
pip install mcp-gs-robot
export GS_CLIENT_ID="<客户端ID>"
export GS_CLIENT_SECRET="<客户端密钥>"
export GS_OPEN_ACCESS_KEY="<访问密钥>"
```

### MCP（stdio）

```sh
mcp-gs-robot
# 注册已安装的可执行文件，继承当前环境变量：
claude mcp add gs-robot -- mcp-gs-robot
```

MCP 使用 stdio 而非 HTTP；参阅 [Claude Code 接入指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md)。

### HTTP + H5

```sh
gs-robot-server
# 浏览器打开 http://localhost:8000/
```

本地开发须先执行 `cd h5 && npm ci && npm run build`；发布的 wheel 已包含静态页面。FastAPI Swagger 地址：`http://localhost:8000/docs`。设置 `GS_SERVER_API_KEY` 后，API 请求需带 `X-API-Key`，H5 可在设置页保存密钥；仅在可信网络及 HTTPS 环境中使用。

### Pi Agent 命令行

```sh
export ANTHROPIC_API_KEY="<密钥>"  # 默认 provider
pi-agent --robot "<机器人SN>"
# 或配置 PI_AGENT_PROVIDER=openai、OPENAI_BASE_URL 和 OPENAI_API_KEY。
```

危险操作默认在终端二次确认。

### Agent Skill

```sh
# 在克隆后的仓库根目录：
mkdir -p ~/.claude/skills
cp -r skills/gs-robot ~/.claude/skills/gs-robot
```

同时挂载 MCP 服务；Codex/WorkBuddy 安装方式见 [Skill 安装指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md)。

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `GS_CLIENT_ID` | 调用真实 API 时 | OpenAPI 客户端 ID |
| `GS_CLIENT_SECRET` | 调用真实 API 时 | OpenAPI 客户端密钥 |
| `GS_OPEN_ACCESS_KEY` | 调用真实 API 时 | OpenAPI 访问密钥 |
| `GS_BASE_URL` | 否 | 上游地址，默认 `https://openapi.gs-robot.com/`，可指向本地 mock |
| `GS_HTTP_TIMEOUT` | 否 | HTTP 超时秒数，默认 `30` |
| `GS_SERVER_API_KEY` | 否 | 设置后受保护的 HTTP 路由要求 `X-API-Key` |
| `GS_SERVER_HOST` | 否 | 监听地址，默认 `0.0.0.0` |
| `GS_SERVER_PORT` | 否 | 监听端口，默认 `8000` |
| `PI_AGENT_PROVIDER` | 否 | `anthropic`（默认）或 `openai` |
| `PI_AGENT_MODEL` | 否 | 默认 Anthropic `claude-opus-5`、OpenAI 兼容 `deepseek-chat` |
| `ANTHROPIC_API_KEY` | Anthropic provider | 模型密钥 |
| `OPENAI_API_KEY` | OpenAI provider | OpenAI 兼容模型密钥 |
| `OPENAI_BASE_URL` | OpenAI provider | OpenAI 兼容接口地址 |
| `PI_AGENT_AUTO_APPROVE` | 否 | `1` 跳过 Agent 二次确认，建议保持未设置 |
| `PI_AGENT_MAX_TURNS` | 否 | 每轮最大工具调用循环数，默认 `12` |

## MCP 工具

下表由 `src/gs_openapi/tools/registry.py` 的 `REGISTRY` 生成，命令：`uv run python -c 'from gs_openapi.tools.registry import REGISTRY; [print(t.name, t.category, t.dangerous, t.description) for t in REGISTRY.values()]'`。共 40 个工具；危险工具在 Agent 中需确认，直接 REST 调用则立即执行。

| 工具 | 分类 | 危险 | 描述 |
|---|---|---|---|
| `list_robots` | robots | 否 | 列出机器人 / List robots |
| `get_robot_status` | robots | 否 | 查询机器人状态 / Get robot status |
| `describe_work_state` | robots | 否 | 解释工作状态 / Describe robot work state |
| `get_robot_capabilities` | robots | 否 | 查询机器人任务能力 / Get task capabilities |
| `list_robot_maps` | maps | 否 | 列出机器人地图 / List robot maps |
| `get_map_canvas` | maps | 否 | 查询地图画布 / Get map canvas |
| `list_charging_positions` | maps | 否 | 列出充电点 / List charging positions |
| `list_map_resources` | maps | 否 | 列出地图资源 / List map resources |
| `list_task_resources` | maps | 否 | 查询任务资源 / List task resources |
| `list_work_modes` | tasks | 否 | 查询工作模式 / List work modes |
| `list_task_definitions` | tasks | 否 | 分页查询任务定义 / List task definitions |
| `get_task_definition` | tasks | 否 | 查询任务定义 / Get task definition |
| `create_task_definition` | tasks | 是 | 创建任务定义 / Create task definition |
| `update_task_definition` | tasks | 是 | 更新任务定义 / Update task definition |
| `delete_task_definition` | tasks | 是 | 删除任务定义 / Delete task definition |
| `start_task` | tasks | 是 | 启动任务 / Start task |
| `pause_task` | tasks | 是 | 暂停任务 / Pause task |
| `resume_task` | tasks | 是 | 继续任务 / Resume task |
| `stop_task` | tasks | 是 | 停止任务 / Stop task |
| `skip_task_item` | tasks | 是 | 跳过任务项 / Skip task item |
| `create_simple_schedule` | schedules | 是 | 创建简易排班 / Create simple schedule |
| `update_simple_schedule` | schedules | 是 | 更新简易排班 / Update simple schedule |
| `delete_simple_schedule` | schedules | 是 | 删除简易排班 / Delete simple schedule |
| `create_schedule` | schedules | 是 | 创建标准排班 / Create schedule |
| `update_schedule` | schedules | 是 | 更新标准排班 / Update schedule |
| `delete_schedule` | schedules | 是 | 删除标准排班 / Delete schedule |
| `list_schedules` | schedules | 否 | 列出排班 / List schedules |
| `get_schedule` | schedules | 否 | 查询排班详情 / Get schedule |
| `get_schedule_calendar` | schedules | 否 | 查询月度排班 / Get schedule calendar |
| `list_schedule_pre_tasks` | schedules | 否 | 查询每日预任务 / List schedule pre-tasks |
| `get_command_status` | commands | 否 | 查询命令投递状态 / Get command delivery status |
| `list_command_history` | commands | 否 | 查询命令历史 / List command history |
| `navigate_home` | commands | 是 | 导航回充电点 / Navigate home |
| `pause_navigation` | commands | 是 | 暂停导航 / Pause navigation |
| `resume_navigation` | commands | 是 | 继续导航 / Resume navigation |
| `stop_navigation` | commands | 是 | 停止导航 / Stop navigation |
| `list_task_reports` | reports | 否 | 分页查询任务报告 / List task reports |
| `get_task_report_map_images` | reports | 否 | 查询报告地图图像 / Get report map images |
| `wait_for_command` | workflows | 否 | 等待命令投递终态 / Wait for command delivery |
| `run_cleaning_task` | workflows | 是 | 创建并启动清洁任务 / Create and start cleaning task |

## REST API

`GET /api/v1/health` 公开；受保护路由包括 `GET /api/v1/robots`、`POST /api/v1/robots/status`、`GET /api/v1/robots/{sn}/status`、`POST /api/v1/tools/{tool_name}`（JSON 输入），以及 `POST /api/v1/agent/sessions` → `POST /api/v1/agent/sessions/{id}/messages`（SSE）。完整路由详见运行时的 [FastAPI Swagger](http://localhost:8000/docs)、[测试指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md)和[上游 V3 接口索引](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md)。SSE 用于 Agent 聊天，不是 MCP 传输协议。

## 安全

Agent/Skill 的危险操作须在移动机器人或修改任务前得到明确授权；`PI_AGENT_AUTO_APPROVE=1` 会跳过确认。REST 直接调用不会再弹确认，应由调用方鉴权并自行确认。严禁将凭据提交仓库或写入日志。先在模拟器/空闲机器人上测试；状态快照可能滞后，命令投递成功不代表任务执行完成。

## 从 0.1.x 迁移

V3 默认工具名已替代原智能路由/旧工具名：`get_robot_status_smart` → `get_robot_status`，`get_task_reports_smart` → `list_task_reports`；启动已存在的任务定义使用 `start_task`，不再用 `create_robot_command`。输入字段为 snake_case，以注册表为准。临时启用旧工具可设置 `GS_ENABLE_LEGACY_TOOLS=1`，旧工具名会带 `legacy_` 前缀。OAuth token 生命周期已按 `expires_in` 正确处理，请移除客户端自行补救逻辑。

## 开发

```sh
uv sync --extra dev
uv run pytest -q
uv run ruff check src tests
cd h5 && npm ci && npm run build
```

H5 构建输出 `src/gs_openapi/server/static/`，运行 `uv build` 前需先构建以打入 wheel。Docker Compose 使用本地 `.env`（从 `.env.example` 复制），不要提交 `.env`。

## 链接

[文档目录](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/README.md) · [V3 接口索引](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) · [测试指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) · [Claude Code/Skill](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md) · [更新日志](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CHANGELOG.md) · [许可证](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)

## 免责声明

本项目仅供个人研究学习，基于公开的高仙 OpenAPI V3 文档，与高仙官方无隶属、认可或支持关系；使用风险自负。请先用模拟器或空闲机器人验证指令，再操作真实设备。
