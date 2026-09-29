<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/logo-dark.svg">
  <img alt="Saodi AI 扫地" src="https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/logo.svg" width="320">
</picture>

<b>扫地僧</b>

**面向高仙清洁机器人的开源运维 Agent —— MCP 服务、REST API、命令行与移动端，基于 OpenAPI V3。**

<sub>包名 <code>mcp-gs-robot</code> · <code>pip install mcp-gs-robot</code></sub>

[![PyPI](https://img.shields.io/pypi/v/mcp-gs-robot.svg)](https://pypi.org/project/mcp-gs-robot/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/cfrs2005/mcp-gs-robot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)

[5 分钟上手](#5-分钟快速启动) · [让 AI Agent 帮你装](#让-ai-agent-帮你装) · [安全机制](#安全机制) · [认知与记忆](#扫地僧的认知与记忆) · [工具](#工具) · [HTTP API 与 H5](#http-api-与-h5) · [配置](#配置) · [排障](#排障) · [English](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md)

</div>

> ⚠️ **免责声明** —— 本项目是**非官方、个人研究学习用途的开源项目**，与高仙（Gausium）官方无任何隶属、认可或支持关系，使用风险自负。机器人指令会让实体机器移动，请先在模拟器或空闲机器人上测试。项目仅依据公开的[高仙 OpenAPI V3 文档](https://developer.gs-robot.com/v3docs/zh_CN/OpenAPI%20V3/Overview)实现。

![H5 页面：扫地僧对话、历史会话、机器人列表、地图与报告](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/h5-showcase_cn.png)

<sub>内置 H5 页面截图，连接 mock 上游，数据为演示数据。</sub>

## 这是什么？

`mcp-gs-robot` 把高仙 OpenAPI **V3**（机器人状态、地图、组合任务、排班、指令、报告）封装成带类型的 Python 客户端，并通过四个入口对外提供，四个入口共用**同一个工具注册表**：

| 入口 | 命令 | 适用场景 |
|---|---|---|
| **MCP 服务**（stdio） | `mcp-gs-robot` | 让 Claude Code、Claude Desktop、Cursor、Cherry Studio 等 MCP 客户端直接操作机器人 |
| **HTTP 服务**（FastAPI） | `gs-robot-server` | 需要 REST 接口、Swagger，以及内置的 **H5 移动端页面** |
| **扫地僧 Saodi**（CLI + H5 对话） | `saodi` | 需要一个会规划、会执行、执行前会确认、还能记住经验的机器人运维助手 |
| **Agent Skill** | `skills/gs-robot/` | 教 Claude Code / Codex / WorkBuddy 正确的操作流程 |

![架构图](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/architecture_cn.svg)

- **42 个工具**：全部 36 个 V3 业务接口、legacy 机器人列表、本地查询（`describe_work_state`、`lookup_error_code`）、本地记忆（`remember`）以及工作流工具（`run_cleaning_task`、`wait_for_command`）
- **类型化、有测试**：pydantic v2 模型、统一信封解包、上游错误（平台码 6 位、机器人任务码 10 位）映射为 `GausiumAPIError`；离线测试套件走 mock HTTP transport
- **安全优先**：所有会让机器人动起来或写数据的工具都标记为 `dangerous`，在 Agent、CLI、H5 中都必须明确确认
- **越用越聪明**：会话、工具调用、错误线程保存在本地 SQLite；经证实的经验写入私有记忆文件，每个新会话都会加载
- **模型无关的 Agent**：默认 Anthropic（`claude-opus-5`），也支持任意 OpenAI 兼容端点（DeepSeek、vLLM、Ollama……）；你用什么语言提问，它就用什么语言回答
- **严格对照官方文档**：[`docs/apis.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) 把每个接口映射到对应官方页面；完整契约见 [`docs/ARCHITECTURE_V3.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md)

## 5 分钟快速启动

**前置条件**：Python 3.12+、[uv](https://docs.astral.sh/uv/)，以及高仙开放平台凭证（在[高仙开发者中心](https://developer.gs-robot.com/)创建应用并申请 AccessKey）。只有想重新构建 H5 时才需要 Node 18+，仓库里已经提交了生产构建。

**1 · 安装**

```bash
git clone https://github.com/cfrs2005/mcp-gs-robot.git
cd mcp-gs-robot
uv sync --extra dev
```

（只需要命令的话也可以 `pip install mcp-gs-robot`，wheel 里自带 H5 构建产物和 Skill。）

**2 · 配置** —— `cp .env.example .env`，然后填写：

| 内容 | 变量 |
|---|---|
| 高仙凭证 | `GS_CLIENT_ID`、`GS_CLIENT_SECRET`、`GS_OPEN_ACCESS_KEY`（填 **AccessKeySecret**，不是 AccessKeyID） |
| 环境 | `GS_BASE_URL` —— 生产 `https://openapi.gs-robot.com/`，测试 `https://openapi.dev.gs-robot.com/` |
| HTTP 服务密钥 | `GS_SERVER_API_KEY` —— 任意足够长的随机串；H5 和 REST 客户端以 `X-API-Key` 发送 |
| LLM（二选一） | Anthropic：`SAODI_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` · OpenAI 兼容：`SAODI_PROVIDER=openai` + `OPENAI_BASE_URL` + `OPENAI_API_KEY` + `SAODI_MODEL` |

所有入口都从**当前工作目录**读取 `.env`；它已被 git 忽略，绝不能提交。真实环境变量优先于 `.env`。

**3 · 启动入口**（在仓库根目录执行）

| 入口 | 命令 | 然后 |
|---|---|---|
| MCP（stdio） | `claude mcp add gs-robot -- uv --directory "$PWD" run mcp-gs-robot` | 在 MCP 客户端里问：*「列出我的机器人，显示电量和工作状态」* |
| REST + H5 | `uv run gs-robot-server` | 打开 `http://localhost:8000/` →「设置」→ 粘贴 `GS_SERVER_API_KEY` → 保存。Swagger：`http://localhost:8000/docs` |
| 扫地僧 CLI | `uv run saodi` | 在终端对话；危险步骤会问 `[y/N]` |
| Skill | `cp -r skills/gs-robot ~/.claude/skills/gs-robot` | 同时挂上 MCP 服务（第 1 行）；Skill 负责教流程 |

确认服务已启动：`curl -s http://127.0.0.1:8000/api/v1/health` → `{"status":"ok", …, "auth_required":true}`。`auth_required: true` 表示 H5 必须先填 key 才能用。

`uv run saodi --show-context` 不需要任何 key 就能打印扫地僧完整的系统提示，可以用来快速确认安装是否成功。

## 让 AI Agent 帮你装

把下面这段粘贴给 Claude Code、Codex 或 Cursor（agent 模式）。它会完成安装、配置、测试和冒烟检查，**全程只调用只读工具**。同一份提示词（附英文版）见 [`docs/AGENT_SETUP_PROMPT.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/AGENT_SETUP_PROMPT.md)。

```text
在这台机器上安装并配置 mcp-gs-robot（高仙 OpenAPI V3 的非官方 MCP / REST / Agent 封装）。
一步一步做，每条命令都把结果给我看，遇到第一个失败就停下。

硬性规则
- 机器人是实体机器。只调用只读工具。绝不调用任何标记为 dangerous 的工具（创建、修改、删除任务或排班，
  启动 / 暂停 / 继续 / 停止 / 跳过任务，导航，组合清洁流程，以及用 `remember` 写记忆）。
- 绝不打印、回显、记录或提交任何凭证。凭证只用文件编辑工具写进 .env（不要用 shell echo），不要把它们
  复述给我，并确认 .env 已被 git 忽略。

步骤
1. 前置条件：`python3 --version`（3.12+）和 `uv --version`。`node --version`（18+）只影响第 5 步。
2. `git clone https://github.com/cfrs2005/mcp-gs-robot.git && cd mcp-gs-robot && uv sync --extra dev`
3. `cp .env.example .env`。向我要 GS_CLIENT_ID、GS_CLIENT_SECRET、GS_OPEN_ACCESS_KEY（填 AccessKeySecret，
   不是 AccessKeyID），并问我 GS_BASE_URL 用生产（https://openapi.gs-robot.com/）还是测试
   （https://openapi.dev.gs-robot.com/）。再问我用哪个 LLM：Anthropic（SAODI_PROVIDER=anthropic +
   ANTHROPIC_API_KEY）或 OpenAI 兼容端点（SAODI_PROVIDER=openai + OPENAI_BASE_URL + OPENAI_API_KEY +
   SAODI_MODEL）。GS_SERVER_API_KEY 由你用
   `python3 -c "import re,secrets,pathlib;p=pathlib.Path('.env');p.write_text(re.sub(r'(?m)^GS_SERVER_API_KEY=.*$','GS_SERVER_API_KEY='+secrets.token_urlsafe(32),p.read_text()))"` 原地写进 .env（不回显 key，我自己去 .env 里看）。
   然后跑 `git check-ignore .env`（必须输出 .env）和 `git status --short`（不能出现 .env）。
4. `uv run pytest -q` 和 `uv run ruff check src tests`，两者都必须通过。
5. 有 Node 18+ 时：`cd h5 && npm ci && npm run build && cd ..`；没有就跳过，
   src/gs_openapi/server/static/ 里已经有预构建的 H5。
6. 后台启动服务，输出写进日志文件：`uv run gs-robot-server > server.log 2>&1 &`
7. `curl -s http://127.0.0.1:8000/api/v1/health` 必须返回 "status":"ok" 和 "auth_required":true。
8. 让我打开 http://localhost:8000/，进入「设置」，粘贴 .env 里 GS_SERVER_API_KEY 的值并保存（应提示连接成功）。
   你自己不要把 key 显示给我。
9. 只读冒烟测试。读取 key 但不打印：
   `KEY=$(grep '^GS_SERVER_API_KEY=' .env | cut -d= -f2-)`
   - `curl -s -X POST -H "X-API-Key: $KEY" -H 'Content-Type: application/json'
     -d '{"page":1,"page_size":5}' http://127.0.0.1:8000/api/v1/tools/list_robots`
   - 从列表里挑一台 "online": true 的机器人，用同样方式调 get_robot_status，
     body 为 {"robot_sn_list":["<该 SN>"]}。
   错误含义：401 = X-API-Key 缺失或错误；110003 = 当前凭证没有绑定这台机器人（不是「没有数据」）；
   230003 = 机器人离线；100026 = 限流，放慢速度。
10. 汇报：工具版本、pytest / ruff 结果、health 响应、在线 / 离线机器人数量，以及遇到的错误（格式 `<码> <msg>`）。
    不要包含任何密钥和 trace ID。
```

## 各入口详解

<details open>
<summary><b>MCP 服务 —— Claude Code / Claude Desktop / Cursor</b></summary>

从源码目录启动（读取仓库里的 `.env`）：

```bash
claude mcp add gs-robot -- uv --directory /path/to/mcp-gs-robot run mcp-gs-robot
```

用 `pip install mcp-gs-robot` 安装时，显式传入凭证 —— 写在 `claude_desktop_config.json` / Cursor 的 MCP 设置里：

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

传输方式为 **stdio**。MCP 宿主会直接执行工具，请保持宿主自己的工具审批提示开启，尤其是危险工具。设置 `GS_ENABLE_LEGACY_TOOLS=1` 可额外以 `legacy_*` 名称暴露 0.1.x 旧工具。

</details>

<details>
<summary><b>HTTP 服务 + H5 移动端</b></summary>

```bash
uv run gs-robot-server              # http://0.0.0.0:8000（GS_SERVER_HOST / GS_SERVER_PORT）
```

- **H5 页面**：手机或浏览器打开 `http://localhost:8000/`，然后在「设置」里填 API Key
- **Swagger**：`http://localhost:8000/docs`
- **Docker**：`cp .env.example .env && $EDITOR .env && docker compose up -d`（监听 `:8000`）

</details>

<details>
<summary><b>扫地僧（Saodi）—— 在终端里对话</b></summary>

```bash
uv run saodi                                   # provider 和 key 来自 .env
uv run saodi --robot <robot-sn>                # 本次会话只操作这一台
uv run saodi --show-context                    # 打印系统提示后退出（不需要 key）
```

```
you> 大堂那台机器人空闲吗？电量够跑一整轮尘推吗？
⚙ get_robot_status(robot_sn_list=["<robot-sn>"])
在线，电量 82%，在地图「大堂」上空闲（IDLE），可以开始。
you> 启动大堂尘推任务
⚙ list_task_definitions(...)
Approve start_task robot_sn=<robot-sn> fusion_task_id=…? [y/N] y
⚙ start_task(...)  ⚙ wait_for_command(...)
命令已下发（cmdStatus=6），还不代表完成 —— 约 30 秒后我再查一次 workState。
```

其他子命令（不需要 LLM key，不连上游）：

```bash
uv run saodi memory                            # 本地记忆文件的路径和内容
uv run saodi memory add "<经验>" [--scope S]   # 手动加一条经验
uv run saodi memory edit                       # 用 $VISUAL / $EDITOR 打开
uv run saodi errors [--status open] [--json]   # 工具调用日志里的错误线程
uv run saodi errors show <id>                  # 单个线程及最近的调用
uv run saodi errors promote <id>               # 把线程提炼为一条记忆
```

> 0.2.0 之后改名：旧命令 `pi-agent` 和 `PI_AGENT_*` 变量在一个版本内仍然可用，并会打印弃用提示。

</details>

<details>
<summary><b>Agent Skill —— Claude Code / Codex / WorkBuddy</b></summary>

```bash
cp -r skills/gs-robot ~/.claude/skills/gs-robot     # Claude Code（用户级）
cp -r skills/gs-robot ~/.codex/skills/gs-robot      # Codex CLI
```

Skill 固化了安全的操作流程（状态 → 能力 → 资源 → 任务定义 → 启动 → 轮询），并附带工作状态、命令类型、任务启动错误码等参考表。详见 [`skills/gs-robot/README.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md)。

</details>

## 安全机制

会让机器人动起来或写数据的工具都以 `dangerous=True` 注册。扫地僧不会自行执行它们：先发出 `confirm_required` 然后等待 —— 终端里是 `[y/N]`，H5 里是按钮，REST 里是 `POST …/confirm`。被拒绝的调用永远不会到达机器人（或记忆文件）。

![危险工具确认流程](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/confirm-flow_cn.svg)

需要记住：

- **下发不等于完成。** `cmdStatus=6` 只表示机器人收到了命令；之后用 `get_robot_status` 或任务报告跟进。
- **REST 直接执行。** `POST /api/v1/tools/{name}` 视调用方已经确认 —— 请在你自己的客户端里做确认。`SAODI_AUTO_APPROVE=1` 会关闭 Agent 的确认（不推荐）。

常见的「清扫这几个区域」场景，`run_cleaning_task` 把整个流程打包成一次确认调用：

![run_cleaning_task 流程](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/cleaning-workflow_cn.svg)

## 扫地僧的认知与记忆

每个新会话生成一份系统提示，按下表顺序拼接，并在该会话内固定（`saodi --show-context` 可打印）：

| 层 | 位置 | 谁维护 | 是否公开 |
|---|---|---|---|
| **Soul** —— 身份、语气（按用户语言回复）、安全底线、何时提议 `remember` | `src/gs_openapi/agent/soul.md` | 项目维护者 | 开源 |
| **Knowledge** —— 领域模型、操作流程、工作状态表 | `skills/gs-robot/`（`references/domain.md`、`SKILL.md`、`references/work-states.md`），与 Agent Skill 是同一份文件 | 项目维护者 | 开源 |
| **Memory** —— 实测调用经验 | `skills/gs-robot/references/experience.md` | 贡献者，通过 PR | 开源 |
| **本地记忆** —— 在你这台机器上学到的经验 | `$SAODI_DATA_DIR/memory.md`（默认 `~/.saodi/memory.md`） | 你和扫地僧（`remember`、`saodi memory`、`saodi errors promote`） | 私有，不进 git |
| **私有目录** —— 你另外维护的笔记 | `$SAODI_CONTEXT_DIR/*.md`（按文件名排序） | 你 | 私有 |

官方错误码表（`skills/gs-robot/references/error-codes.md`，约 23 KB）**不再常驻**系统提示：扫地僧遇到不认识的码时调用只读工具 `lookup_error_code`，并被要求不要猜。整个提示受 `SAODI_CONTEXT_MAX_CHARS`（默认 60000）约束；超限时**先删本地记忆里最旧的条目**，并打 WARNING 说明删了几条。

![扫地僧记忆闭环：加载栈与学习闭环](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/memory-loop_cn.svg)

**怎么让它越用越聪明**

1. **对话里 `remember`。** 扫地僧学到经证实、可复用的东西时 —— 某个错误码的真实含义、某台机器人的长期特殊行为、你的偏好 —— 会提议 `remember(lesson)`。它要写文件，所以和其他危险工具一样先征得确认。同意后向 `memory.md` 追加一行 `- [YYYY-MM-DD] lesson`；重复的跳过，看起来像凭证的内容（token / secret / Bearer / 长随机串）一律拒绝。一次性的数据（今天的电量、某次快照）和猜测不记。下一个会话就会加载这一行。
2. **从错误到经验。** 每次工具调用都记在本地，失败按指纹归并成错误线程。`saodi errors` 列出线程，`PATCH /api/v1/errors/threads/{id}` 设置状态、分类和 `note`，`saodi errors promote <id>` 把 note（为空时用分类加样例 msg）写进 `memory.md`，并把线程标记为已提炼。
3. **手动。** `saodi memory add "…"` 或 `saodi memory edit`。
4. **回馈给所有人。** 通用的经验欢迎通过 PR 写进 `experience.md`。写入规则：只写通用现象和处置办法 —— **不写机器人 SN、traceId、requestId、账号、凭证、客户名或站点名**。

## 工具

42 个工具统一定义在 `gs_openapi/tools/`，以完全相同的方式暴露给 MCP、Agent 和 REST（`POST /api/v1/tools/{name}`）。入参为 `snake_case`，注册表负责映射为 V3 的 `camelCase`。**⚠️ = 危险操作。**

| 分类 | 工具 |
|---|---|
| **机器人** | `list_robots` · `get_robot_status` · `describe_work_state` · `get_robot_capabilities` |
| **地图** | `list_robot_maps` · `get_map_canvas` · `list_charging_positions` · `list_map_resources` · `list_task_resources` |
| **任务** | `list_work_modes` · `list_task_definitions` · `get_task_definition` · `create_task_definition` ⚠️ · `update_task_definition` ⚠️ · `delete_task_definition` ⚠️ · `start_task` ⚠️ · `pause_task` ⚠️ · `resume_task` ⚠️ · `stop_task` ⚠️ · `skip_task_item` ⚠️ |
| **排班** | `list_schedules` · `get_schedule` · `get_schedule_calendar` · `list_schedule_pre_tasks` · `create_simple_schedule` ⚠️ · `update_simple_schedule` ⚠️ · `delete_simple_schedule` ⚠️ · `create_schedule` ⚠️ · `update_schedule` ⚠️ · `delete_schedule` ⚠️ |
| **指令** | `get_command_status` · `list_command_history` · `navigate_home` ⚠️ · `pause_navigation` ⚠️ · `resume_navigation` ⚠️ · `stop_navigation` ⚠️ |
| **报告** | `list_task_reports` · `get_task_report_map_images` |
| **工作流** | `wait_for_command` · `run_cleaning_task` ⚠️ |
| **参考** | `lookup_error_code`（本地只读） |
| **记忆** | `remember` ⚠️（写本地记忆文件） |

<details>
<summary><b>各工具入参</b></summary>

**机器人与地图**

| 工具 | 必填 | 可选 | 说明 |
|---|---|---|---|
| `list_robots` | – | `page`、`page_size`、`relation` | legacy `v1alpha1/robots`（V3 没有列表接口） |
| `get_robot_status` | `robot_sn_list`（≤100） | | 附加 `work_state_name` / `work_state_desc`；快照延迟 ≤30 秒 |
| `describe_work_state` | `work_state` | | 本地查表，不调接口 |
| `get_robot_capabilities` | `robot_sn` | | 组合任务 / 排班支持情况 |
| `list_robot_maps` | `robot_sn` | | `mapId`、`mapVersionId`、`displayName` |
| `get_map_canvas` | `robot_sn`、`map_id` | | 临时 PNG 链接 + 栅格元数据 |
| `list_charging_positions` | `robot_sn`、`map_id` | | |
| `list_map_resources` | `robot_sn`、`map_id_list` | `include_paths/regions/positions` | 不含工作模式的地图资源 |
| `list_task_resources` | `robot_sn`、`map_id_list` | `include_paths/regions/positions` | **建任务 / 排班前先查它** |

**任务**

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

**排班**

| 工具 | 必填 | |
|---|---|---|
| `create_simple_schedule` | `robot_sn`、`task_name`、`site_mode`、`work_mode`、`map_resource_list`、`plan_execute_type`、`plan_repeat_type`、`plan_start_date`、`plan_start_time` | ⚠️ |
| `update_simple_schedule` / `delete_simple_schedule` | `robot_sn`、`plan_uuid`、`year`、`month`、`day_of_month`、`operation_type` | ⚠️ |
| `create_schedule` / `update_schedule` / `delete_schedule` | 标准排班字段（见[官方文档](https://developer.gs-robot.com/v3docs/zh_CN/OpenAPI%20V3/Overview)） | ⚠️ |
| `list_schedules` | `robot_sn` | |
| `get_schedule` | `robot_sn`、`plan_uuid`、`year`、`month`、`day_of_month` | |
| `get_schedule_calendar` | `robot_sn`、`year_month` | |
| `list_schedule_pre_tasks` | `robot_sn`、`date` | |

**指令、报告、工作流、参考与记忆**

| 工具 | 必填 | 可选 | |
|---|---|---|---|
| `get_command_status` | `robot_sn`、`request_id` | | `cmdStatus=6` = 已下发，**不是**已完成 |
| `list_command_history` | `robot_sn` | `page`、`pagesize`、`cmd_status`、`command_type` | |
| `navigate_home` | `robot_sn`、`map_id` | `map_resource_id` | ⚠️ |
| `pause_navigation` / `resume_navigation` / `stop_navigation` | `robot_sn` | | ⚠️ |
| `list_task_reports` | `robot_sn` | `page`、`pagesize`、`end_time_min`、`end_time_max` | |
| `get_task_report_map_images` | `task_report_id` | `robot_sn` | |
| `wait_for_command` | `robot_sn`、`request_id` | `timeout_seconds` | 轮询到 `cmdStatus` 终态 |
| `run_cleaning_task` | `robot_sn`、`task_name`、`map_id`、`resource_ids` | `mode`、`strength`、`loop_count`、`wait_seconds` | ⚠️ 能力 → 资源 → 创建 → 启动 → 轮询 |
| `lookup_error_code` | `code`（3–10 位数字） | | 返回 `error-codes.md` 的匹配行和 `experience.md` 的相关条目；查不到时 `found: false` 并提示「不要猜」 |
| `remember` | `lesson` | `scope` | ⚠️ 向 `$SAODI_DATA_DIR/memory.md` 追加 `- [YYYY-MM-DD] lesson`；去重，拒绝看起来像凭证的内容 |

</details>

从注册表重新生成列表：

```bash
uv run python -c "from gs_openapi.tools.registry import REGISTRY; [print(t.category, t.name, '⚠️' if t.dangerous else '') for t in REGISTRY.values()]"
```

## HTTP API 与 H5

统一前缀 `/api/v1`。`GET /health` 公开；设置了 `GS_SERVER_API_KEY` 时其余接口都需要 `X-API-Key`。错误统一为 `{"error": {"code", "message", "trace_id"}}`；上游 V3 错误转为 HTTP 502，并带上业务码。

| 领域 | 路由 |
|---|---|
| 健康与鉴权 | `GET /health`（公开；`auth_required` 告诉客户端是否需要 key，绝不返回 key 本身）· `GET /auth/check`（校验 key，不打上游） |
| 工具 | `POST /tools/{tool_name}` —— 用 JSON 入参调用任意注册表工具 |
| 机器人 | `GET /robots` · `POST /robots/status` · `GET /robots/{sn}/status` · `/capabilities` · `/work-modes` |
| 地图 | `GET /robots/{sn}/maps` · `/maps/{map_id}/canvas` · `/maps/{map_id}/resources` |
| 任务 | `GET/POST /robots/{sn}/task-definitions` · `GET/PUT/DELETE …/{fusion_task_id}` · `POST /robots/{sn}/tasks/{start\|pause\|resume\|stop\|skip}` |
| 导航 | `POST /robots/{sn}/navigation/{go-home\|pause\|resume\|stop}` |
| 指令与报告 | `GET /robots/{sn}/commands` · `…/commands/{request_id}` · `GET /robots/{sn}/reports` |
| 排班 | `GET/POST /robots/{sn}/schedules` · `POST …/schedules/simple` · `GET/PUT/DELETE …/schedules/{plan_id}` |
| Agent | `GET/POST /agent/sessions` · `GET/DELETE /agent/sessions/{id}` · `POST …/{id}/messages`（**SSE**）· `POST …/{id}/confirm` |
| 错误线程 | `GET /errors/threads` · `GET/PATCH /errors/threads/{id}` |

`/messages` 的 SSE 事件：`text_delta` · `tool_call` · `tool_result` · `confirm_required` · `done` · `error`。会话保存在 SQLite，服务重启后对话可以继续。

```bash
KEY=$(grep '^GS_SERVER_API_KEY=' .env | cut -d= -f2-)
SID=$(curl -s -XPOST -H "X-API-Key: $KEY" localhost:8000/api/v1/agent/sessions | jq -r .session_id)
curl -N -XPOST -H "X-API-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"content":"列出我的机器人和电量"}' \
  localhost:8000/api/v1/agent/sessions/$SID/messages
```

**H5**（`h5/`，Vue 3 + Vite + Vant）：**对话**（流式 Markdown、HTML 预览、工具调用时间线、确认按钮、历史抽屉）、**机器人**（在线 / 离线 / 不可达三态、电量、工作状态）、**详情**（地图与画布、任务定义、快捷操作、报告；离线机器人显示横幅而不是报错）、**设置**（API 地址、API Key、语言）。服务端要求 key 而本地没填时，H5 会引导你去设置页。生产构建已提交在 `src/gs_openapi/server/static/`，`pip install` 即可带上。

### 多语言

- **H5**：支持 English / 中文，在「设置 → 语言」切换（首次访问跟随浏览器语言）。
- **扫地僧**：用你提问的语言回答；`workState`、`cmdStatus` 等字段名保留英文。
- **文档**：以英文为主；本文件是 [README.md](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md) 的中文对照版。工具描述为中英双语。

## 配置

| 变量 | 默认值 | 说明 |
|---|---|---|
| `GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` | – | **必填。** 高仙应用与 AccessKey 凭证（`GS_OPEN_ACCESS_KEY` 填 AccessKeySecret） |
| `GS_BASE_URL` | `https://openapi.gs-robot.com/` | 上游地址；测试环境 `https://openapi.dev.gs-robot.com/`，也可指向 mock |
| `GS_HTTP_TIMEOUT` | `30` | HTTP 超时（秒） |
| `GS_ENABLE_LEGACY_TOOLS` | 未设置 | `1` 时 MCP 服务额外以 `legacy_*` 注册 0.1.x 工具 |
| `GS_SERVER_HOST` / `GS_SERVER_PORT` | `0.0.0.0` / `8000` | HTTP 服务监听地址 |
| `GS_SERVER_API_KEY` | 未设置 | 设置后受保护接口需要 `X-API-Key` |
| `SAODI_PROVIDER` | `anthropic` | `anthropic` 或 `openai` |
| `SAODI_MODEL` | `claude-opus-5` / `deepseek-chat` | 各 provider 的模型 ID |
| `ANTHROPIC_API_KEY` | – | Anthropic provider 的 key |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | – | OpenAI 兼容 provider |
| `SAODI_AUTO_APPROVE` | `0` | `1` 时跳过危险工具确认（包括 `remember`） |
| `SAODI_MAX_TURNS` | `12` | 每条用户消息最多的工具轮数（工具结果截断到 2 万字符） |
| `SAODI_DATA_DIR` | `~/.saodi` | 本地数据：`saodi.sqlite`（会话、工具调用日志、错误线程）和 `memory.md`（本地记忆） |
| `SAODI_CONTEXT_DIR` | 未设置 | 私有 `*.md` 笔记目录，追加到系统提示末尾 |
| `SAODI_CONTEXT_MAX_CHARS` | `60000` | 系统提示长度上限；先删最旧的本地记忆条目，再截断，并打 WARNING |

弃用的旧名：新名未设置时还会再读一个版本（每个旧名打一次 WARNING，只记变量名）：

| 新名 | 旧名（弃用） |
|---|---|
| `SAODI_PROVIDER` | `PI_AGENT_PROVIDER` |
| `SAODI_MODEL` | `PI_AGENT_MODEL` |
| `SAODI_AUTO_APPROVE` | `PI_AGENT_AUTO_APPROVE` |
| `SAODI_MAX_TURNS` | `PI_AGENT_MAX_TURNS` |
| `saodi`（命令） | `pi-agent` |

## 排障

| 现象 | 原因 | 处理 |
|---|---|---|
| H5 或 curl 返回 **401** | 设置了 `GS_SERVER_API_KEY`，但客户端没发或发错了 `X-API-Key` | H5：设置页粘贴 key → 保存（会调用 `/api/v1/auth/check` 校验）。curl：加 `-H "X-API-Key: …"`。`GET /api/v1/health` 的 `auth_required` 可以看是否需要 key |
| **110003** `Robot is not bound to the current user.` | 当前开放平台应用没有绑定这台机器人（或没有这类数据的权限） | 这**不等于**「没有数据」。看这台 SN 在不在 `list_robots` 里；不在就去开放平台把机器人绑定到应用。报告接口可能报 110003，而状态接口正常 |
| **230003** `Robot … routing failed.` | 机器人离线 / 长时间没连云 | 看 `onlineStatus` 或 `list_robots` 的 `online` 字段；换别的接口重试也没用。一台这样的机器人会让整批状态查询失败，REST 的机器人列表已自动降级为逐台查询 |
| **100026** | 限流（约 20 次/秒） | 放慢速度，避免并发突发 |
| 参数正确仍然 **422** | 可能是上游字段漂移（响应与本地模型不一致） | 运行 `uv run saodi errors` —— `response_model` / `our_bug` 线程会指出要修的模型；欢迎提 issue |
| 明明有 `.env` 却提示凭证缺失 | `.env` 从**当前工作目录**读取；真实环境变量优先于 `.env` | 在 `.env` 所在目录执行命令（MCP 用 `uv --directory <repo> run mcp-gs-robot`），或在 MCP 的 `env` 里传变量；用 `env \| grep '^GS_'` 检查有没有残留的旧环境变量 |
| 出现 `PI_AGENT_* 已弃用` 警告 | `.env` 里还是旧变量名 | 改成 `SAODI_*` |

## 开发

```
src/gs_openapi/
├── auth/token_manager.py      OAuth token（毫秒级过期时间、加锁刷新）
├── core/                      HTTP 客户端、V3 端点注册、错误类型
├── v3/                        GausiumV3 门面 · pydantic 模型 · 参考表
├── tools/                     工具注册表（MCP / Agent / REST 的唯一来源）+ 知识类工具
├── mcp/                       FastMCP 服务（v3_server.py）+ legacy_tools.py
├── agent/                     扫地僧核心、soul.md、系统提示拼装、providers、会话、CLI
├── store/                     SQLite 会话 / 工具调用日志 / 错误线程，本地 memory.md
├── server/                    FastAPI 应用、路由、SSE、H5 静态托管
└── main.py                    `mcp-gs-robot` stdio 入口
h5/                            Vue 3 移动端页面（构建到 server/static）
skills/gs-robot/               Agent Skill + 参考资料（也是扫地僧的 Knowledge / Memory）
docs/ARCHITECTURE_V3.md        所有模块遵循的契约
tests/                         离线测试（httpx.MockTransport，无网络）
```

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check src tests
cd h5 && npm ci && npm run build    # 重新构建 H5 到 src/gs_openapi/server/static
uv build                            # wheel 包含 H5 产物和 Skill
```

新增 V3 工具：在 `src/gs_openapi/tools/v3_tools.py` 里用 `@tool(...)` 定义入参模型和 handler，MCP、REST、Agent 会自动识别。补测试，并在工具表里加一行。约定见 [`CLAUDE.md`](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CLAUDE.md)；curl 演练和 MCP Inspector 用法见[测试指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md)。

<details>
<summary><b>从 0.1.x 迁移</b></summary>

| 0.1.x | 0.2.0+ |
|---|---|
| `get_robot_status_smart`、`get_robot_status`（按 SN 前缀路由 v1/v2） | `get_robot_status`（V3 快照，任意系列，批量 ≤100） |
| `get_task_reports_smart`、`list_robot_task_reports` | `list_task_reports` |
| `create_robot_command`（start/pause/stop） | `start_task` / `pause_task` / `resume_task` / `stop_task`、`navigate_home` |
| `submit_temp_site_task`、`execute_*_workflow` | `create_task_definition` + `start_task`，或 `run_cleaning_task` |
| `list_robot_maps`（openapi/v1） | `list_robot_maps`（V3）+ `list_task_resources` |

设置 `GS_ENABLE_LEGACY_TOOLS=1` 后旧工具仍以 `legacy_*` 名称可用。OAuth `expires_in` 的 bug（把毫秒时间戳当成秒）已修复，可以去掉各种刷新绕行代码。

</details>

## 文档

| 文档 | 用途 |
|---|---|
| [架构契约](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/ARCHITECTURE_V3.md) | 工具名、REST/SSE 协议、Agent 接口、认知分层、本地存储 |
| [Agent 安装提示词](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/AGENT_SETUP_PROMPT.md) | 可直接复制给 Claude Code / Codex / Cursor 的提示词（English + 中文） |
| [V3 接口索引](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/apis.md) | 每个接口的方法、路径、固件支持情况和官方页面链接 |
| [Claude Code 集成](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/CLAUDE_CODE_INTEGRATION.md) | MCP 配置 + Skill |
| [测试指南](https://github.com/cfrs2005/mcp-gs-robot/blob/main/docs/TESTING_GUIDE.md) | 单元测试、curl 演练、MCP Inspector |
| [Skill 说明](https://github.com/cfrs2005/mcp-gs-robot/blob/main/skills/gs-robot/README.md) | 在 Claude Code / Codex / WorkBuddy 中安装 Skill |
| [更新日志](https://github.com/cfrs2005/mcp-gs-robot/blob/main/CHANGELOG.md) | 版本说明 |

## 参与贡献

Fork 仓库、新建分支、`uv sync --extra dev`，改动附带测试，运行 `uv run pytest -q && uv run ruff check src tests`，改了注册表就同步更新工具表，然后提 Pull Request。欢迎为 `experience.md` 贡献经验 —— 只写通用现象，不写 SN、traceId、账号、凭证、客户名或站点名。

## 许可证

MIT —— 见 [LICENSE](https://github.com/cfrs2005/mcp-gs-robot/blob/main/LICENSE)。

## 免责声明

本项目是**非官方、个人研究学习用途的开源项目**，仅依据高仙公开的 OpenAPI V3 文档实现，与高仙官方无任何隶属、认可或支持关系。不提供任何形式的担保；你需要对自己下发指令的机器人负责。请始终先在模拟器或空闲机器上验证，不要把凭证放进版本控制，并记住：命令已下发（`cmdStatus=6`）不等于任务已完成。

<div align="center">

*献给宁愿直接问机器人、也不想在控制台里点来点去的人。*

</div>
