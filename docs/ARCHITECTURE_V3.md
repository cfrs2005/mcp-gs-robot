# mcp-gs-robot V3 架构与接口契约

> 本文是 V3 重构（v0.2.0）的**唯一契约来源**。所有子模块（core / tools / mcp / agent / server / h5 / skill）都必须遵守这里定义的名字与数据形状。修改契约先改本文。

## 1. 总体分层

```
┌──────────────────────────────────────────────────────────────┐
│  入口层                                                       │
│  ├─ MCP Server  (stdio)   gs_openapi.main / mcp-gs-robot      │
│  ├─ HTTP Server (FastAPI) gs_openapi.server / gs-robot-server │
│  │     ├─ REST  /api/v1/...                                   │
│  │     ├─ Agent SSE /api/v1/agent/...                         │
│  │     └─ H5 静态页 /  (由 h5/ 构建产物提供)                   │
│  ├─ Pi Agent CLI          gs_openapi.agent.cli / pi-agent     │
│  └─ Skill                 skills/gs-robot/SKILL.md            │
├──────────────────────────────────────────────────────────────┤
│  工具注册表  gs_openapi.tools.registry  (单一真源)             │
│    ToolSpec(name, description, input_model, handler, dangerous)│
│    → MCP tool / Agent tool schema / REST handler 共用           │
├──────────────────────────────────────────────────────────────┤
│  Pi Agent 核心  gs_openapi.agent.core                          │
│    provider = anthropic (默认 claude-opus-5) | openai_compat    │
├──────────────────────────────────────────────────────────────┤
│  V3 客户端  gs_openapi.v3.api.GausiumV3  (+ models / references)│
│  统一 HTTP  gs_openapi.core.client.GausiumAPIClient            │
│  Token      gs_openapi.auth.token_manager                      │
└──────────────────────────────────────────────────────────────┘
```

依赖方向只能向下。`server` 与 `mcp` 不直接调用 `httpx`；一律走 `GausiumV3`。

## 2. 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` | 是 | Gausium 开放平台凭据 |
| `GS_BASE_URL` | 否 | 默认 `https://openapi.gs-robot.com/` |
| `GS_HTTP_TIMEOUT` | 否 | 秒，默认 30 |
| `GS_SERVER_API_KEY` | 否 | 设置后 HTTP Server 要求 `X-API-Key` 头（H5 通过设置页保存到 localStorage） |
| `GS_SERVER_HOST` / `GS_SERVER_PORT` | 否 | 默认 `0.0.0.0` / `8000` |
| `PI_AGENT_PROVIDER` | 否 | `anthropic`（默认）或 `openai` |
| `PI_AGENT_MODEL` | 否 | 默认 anthropic→`claude-opus-5`；openai→`deepseek-chat` |
| `ANTHROPIC_API_KEY` | provider=anthropic 时 | Anthropic SDK 自动读取 |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | provider=openai 时 | 任意 OpenAI 兼容端点 |
| `PI_AGENT_AUTO_APPROVE` | 否 | `1` 时危险操作不再二次确认 |
| `PI_AGENT_MAX_TURNS` | 否 | 单轮对话最大工具循环次数，默认 12 |

## 3. 工具注册表（MCP 工具名 = Agent 工具名 = REST 语义）

`gs_openapi/tools/registry.py`

```python
@dataclass
class ToolSpec:
    name: str                      # 见下表
    description: str               # 面向模型的说明（中英双语一句话）
    input_model: type[BaseModel]   # pydantic v2；字段用 snake_case
    handler: Callable[[GausiumV3, BaseModel], Awaitable[Any]]
    dangerous: bool = False        # True 时 Agent 需用户确认
    category: str = "robots"

REGISTRY: dict[str, ToolSpec]
def get_tool(name) -> ToolSpec
def list_tools(category: str | None = None) -> list[ToolSpec]
async def invoke(name: str, args: dict, v3: GausiumV3) -> Any   # 校验 + 调用，返回可 JSON 序列化对象
def to_anthropic_tools() -> list[dict]     # {"name","description","input_schema"}
def to_openai_tools() -> list[dict]        # {"type":"function","function":{...}}
```

| 分类 | 工具名 | 输入（snake_case） | dangerous | V3 端点 |
|---|---|---|---|---|
| robots | `list_robots` | page=1, page_size=20, relation? | | legacy `GET v1alpha1/robots`（V3 无列表接口） |
| robots | `get_robot_status` | robot_sn_list: list[str] (≤100) | | robots/status/get；返回附加 `work_state_name`、`work_state_desc` |
| robots | `describe_work_state` | work_state: int | | 本地参考表 |
| robots | `get_robot_capabilities` | robot_sn | | tasks/fusion/robot-capabilities/get |
| maps | `list_robot_maps` | robot_sn | | robots/maps/list |
| maps | `get_map_canvas` | robot_sn, map_id | | robots/maps/canvas/get |
| maps | `list_charging_positions` | robot_sn, map_id? | | maps/charging-positions/list |
| maps | `list_map_resources` | robot_sn, map_id_list | | maps/map-resources/list |
| maps | `list_task_resources` | robot_sn, map_id_list, include_paths=True, include_regions=True, include_positions=False | | maps/schedule-resources/list |
| tasks | `list_work_modes` | robot_sn | | tasks/fusion/work-modes/list |
| tasks | `list_task_definitions` | robot_sn, page=1, pagesize=20 | | tasks/persistence/page |
| tasks | `get_task_definition` | robot_sn, fusion_task_id | | tasks/persistence/get |
| tasks | `create_task_definition` | robot_sn, task_name, work_mode: dict, map_resource_list: list[dict], loop_count?, site_id?, task_advance_config? | ✔ | tasks/persistence/create |
| tasks | `update_task_definition` | 同上 + fusion_task_id | ✔ | tasks/persistence/update |
| tasks | `delete_task_definition` | robot_sn, fusion_task_id | ✔ | tasks/persistence/delete |
| tasks | `start_task` | robot_sn, fusion_task_id, loop_count? | ✔ | robots/commands/tasks/start |
| tasks | `pause_task` / `resume_task` / `stop_task` / `skip_task_item` | robot_sn | ✔ | robots/commands/tasks/{pause,resume,stop,skip} |
| schedules | `create_simple_schedule` | 按 simple/create 文档字段（snake_case） | ✔ | schedules/plans/simple/create |
| schedules | `update_simple_schedule` / `delete_simple_schedule` | + plan_uuid | ✔ | schedules/plans/simple/{update,delete} |
| schedules | `create_schedule` / `update_schedule` / `delete_schedule` | 按标准 schedule 文档 | ✔ | schedules/plans/{create,update,delete} |
| schedules | `list_schedules` / `get_schedule` | robot_sn, page…/ plan id | | schedules/plans/{list,get} |
| schedules | `get_schedule_calendar` | robot_sn, year_month | | schedules/plans/calendar/month/get |
| schedules | `list_schedule_pre_tasks` | robot_sn, date | | schedules/plans/pre-tasks/day/list |
| commands | `get_command_status` | robot_sn, request_id | | robots/commands/status/get |
| commands | `list_command_history` | robot_sn, page=1, pagesize=20 … | | robots/commands/status/page |
| commands | `navigate_home` | robot_sn, (文档要求的其它字段) | ✔ | robots/commands/navigation/go-home |
| commands | `pause_navigation` / `resume_navigation` / `stop_navigation` | robot_sn | ✔ | robots/commands/navigation/{pause,resume,stop} |
| reports | `list_task_reports` | robot_sn, page=1, pagesize=20, end_time_min?, end_time_max? | | taskreports/page |
| reports | `get_task_report_map_images` | 按文档字段 | | taskreports/map-images/query |
| workflows | `run_cleaning_task` | robot_sn, task_name, map_id, resource_ids: list[str], mode="sweep", strength?, loop_count=1, wait_seconds=30 | ✔ | 组合：capabilities→task_resources→create_task_definition→start_task→轮询 get_command_status |
| workflows | `wait_for_command` | robot_sn, request_id, timeout_seconds=60 | | 轮询 commands/status/get 直到 cmdStatus 终态 |

工具输入字段名一律 snake_case，`handler` 内部映射为文档的 camelCase。返回值统一为 `dict`/`list`（pydantic → `model_dump(by_alias=False)`），错误抛 `GausiumAPIError`，由各入口层转换。

## 4. HTTP Server（FastAPI）

- 启动：`gs-robot-server`（entry point）或 `uvicorn gs_openapi.server.app:app`。
- 前缀 `/api/v1`；所有响应 JSON；错误统一 `{"error": {"code": <int|str>, "message": str, "trace_id": str|null}}`。上游 `GausiumAPIError` → HTTP 502（code 为六位业务码），参数错误 → 422/400，鉴权失败 → 401。
- CORS：默认允许所有来源（H5 同源部署时无影响）。
- `GET /api/v1/health` → `{"status":"ok","version":"0.2.0","agent_provider":"anthropic","tools":<int>}`
- 通用工具调用（REST 与工具注册表一一对应）：`POST /api/v1/tools/{tool_name}`，body = 工具输入 JSON，返回 `{"result": ...}`。危险工具在 REST 下直接执行（调用方即已确认）。
- 友好路由（内部也走注册表）：
  - `GET /api/v1/robots?page&page_size` → 机器人数组；legacy 列表的 `serialNumber` 会补齐为 `robotSn`（H5 以此为键）
  - `POST /api/v1/robots/status` `{robot_sn_list}`；`GET /api/v1/robots/{sn}/status`
  - `GET /api/v1/robots/{sn}/maps`；`GET /api/v1/robots/{sn}/maps/{map_id}/canvas`；`GET /api/v1/robots/{sn}/maps/{map_id}/resources`
  - `GET /api/v1/robots/{sn}/capabilities`；`GET /api/v1/robots/{sn}/work-modes`
  - `GET /api/v1/robots/{sn}/task-definitions?page&pagesize`；`POST` 创建；`GET/PUT/DELETE /api/v1/robots/{sn}/task-definitions/{fusion_task_id}`
  - `POST /api/v1/robots/{sn}/tasks/{start|pause|resume|stop|skip}`
  - `POST /api/v1/robots/{sn}/navigation/{go-home|pause|resume|stop}`
  - `GET /api/v1/robots/{sn}/commands?page&pagesize`；`GET /api/v1/robots/{sn}/commands/{request_id}`
  - `GET /api/v1/robots/{sn}/reports?page&pagesize&end_time_min&end_time_max`
  - `GET/POST /api/v1/robots/{sn}/schedules`；`POST /api/v1/robots/{sn}/schedules/simple`；`GET/PUT/DELETE /api/v1/robots/{sn}/schedules/{plan_id}`
- Agent：
  - `POST /api/v1/agent/sessions` `{ "title"?: str }`（body 可省略）→ `{"session_id": str}`
  - `GET /api/v1/agent/sessions/{id}` → `{"session_id", "messages":[{"role","content","tool_calls"?}], "created_at"}`
  - `DELETE /api/v1/agent/sessions/{id}`
  - `POST /api/v1/agent/sessions/{id}/messages` `{ "content": str }` → **SSE**（`text/event-stream`），每行 `data: <json>`，事件类型：
    - `{"type":"text_delta","text":str}`
    - `{"type":"tool_call","id":str,"name":str,"input":dict}`
    - `{"type":"tool_result","id":str,"name":str,"output":any,"is_error":bool}`
    - `{"type":"confirm_required","confirm_id":str,"name":str,"input":dict,"summary":str}` —— 流暂停，等待确认（最长 120s，超时视为拒绝）
    - `{"type":"done","message_id":str,"usage":{...}}`
    - `{"type":"error","message":str}`
  - `POST /api/v1/agent/sessions/{id}/confirm` `{ "confirm_id": str, "approve": bool }` → `{"ok": true}`
- 静态：`/`、`/index.html`、`/assets/*` 由 `src/gs_openapi/server/static/`（H5 构建产物）提供；目录不存在时 `/` 返回简短提示 JSON。

## 5. Pi Agent 接口（供 server 与 CLI 调用）

`gs_openapi/agent/core.py`

```python
class AgentEvent(TypedDict): type: str; ...   # 与 SSE 事件同形
class ConfirmGate(Protocol):
    async def ask(self, session_id: str, confirm_id: str, name: str, input: dict, summary: str) -> bool: ...

class PiAgent:
    def __init__(self, v3: GausiumV3, provider: LLMProvider, *, auto_approve: bool = False, max_turns: int = 12, confirm_gate: ConfirmGate | None = None): ...
    async def run(self, session: AgentSession, user_text: str) -> AsyncIterator[AgentEvent]: ...

class AgentSession:  # 内存态，可序列化
    session_id: str; messages: list[dict]; created_at: float
class SessionStore: create()/get()/delete()  # 内存实现 InMemorySessionStore

class LLMProvider(Protocol):
    async def stream(self, *, system: str, messages: list[dict], tools: list[dict]) -> AsyncIterator[ProviderEvent]: ...
    # ProviderEvent: text_delta | tool_use(id,name,input) | message_end(stop_reason, usage, assistant_content)
```

- `providers/anthropic.py`：`anthropic.AsyncAnthropic()`，`client.messages.stream(model, max_tokens=16000, system=[{type:text,text,cache_control:{type:ephemeral}}], tools=..., thinking={"type":"adaptive"}, messages=...)`；用 `stream.get_final_message()` 取完整 assistant content 回填历史；工具结果以一条 user 消息内多个 `tool_result` 返回。
- `providers/openai_compat.py`：`httpx` 调 `{OPENAI_BASE_URL}/chat/completions`（`stream=true`，`tools`），兼容 DeepSeek 等。
- 系统提示：中文为主，说明机器人运维助手角色、工具使用规范（先查能力/资源再下发任务）、危险操作必须确认、回答简洁。
- CLI：`pi-agent`（`gs_openapi/agent/cli.py`）：终端 REPL，`--provider/--model`，危险操作在终端 y/N 确认。

## 6. H5（`h5/`，Vue 3 + Vite + TypeScript + Vant 4）

- 构建产物输出到 `src/gs_openapi/server/static/`（`vite.config.ts` 的 `build.outDir`，`base: './'`）。产物纳入 wheel（`pyproject` 的 `[tool.hatch.build.targets.wheel]` 不需改，因为在包目录内）。
- 页面（底部 Tabbar）：`/chat` Pi Agent 聊天（SSE 流式、工具调用折叠卡片、confirm_required 弹确认按钮）、`/robots` 机器人列表（状态卡：在线、电量、工作状态名、当前地图）、`/robots/:sn` 详情（地图列表+画布图、能力、任务定义、快捷操作 开始/暂停/继续/停止/回充 带确认弹窗、最近报告）、`/settings`（API Base、API Key 保存到 localStorage）。
- 与后端通信：`fetch`；SSE 用 `fetch` + `ReadableStream` 逐行解析 `data:`。
- 开发：`npm run dev` 通过 Vite proxy 转发 `/api` 到 `http://127.0.0.1:8000`。

## 7. Skill（`skills/gs-robot/SKILL.md`）

Agent Skill（Claude Code / Codex / WorkBuddy 通用格式：YAML frontmatter `name`、`description` + 正文）。内容：何时使用、环境变量、通过 MCP 工具操作机器人的标准流程（查状态 → 查能力/资源 → 建任务定义 → 启动 → 轮询命令状态）、安全边界（危险工具需确认）、常见错误码处理、`references/` 里放工具速查表与工作状态表。

## 8. 版本与兼容

- 版本 `0.2.0`。V3 为默认工具集；旧版工具保留在 `gs_openapi/mcp/legacy_tools.py`，通过 `GS_ENABLE_LEGACY_TOOLS=1` 注册（名称加 `legacy_` 前缀），避免与 V3 工具名冲突。
- `python -m gs_openapi.main` / `mcp-gs-robot` 仍为 MCP stdio 入口。
