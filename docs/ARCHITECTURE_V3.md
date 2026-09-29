# mcp-gs-robot V3 架构与接口契约

> 本文是 V3 重构（v0.2.0 起）的**唯一契约来源**。所有子模块（core / tools / mcp / agent / server / h5 / skill）都必须遵守这里定义的名字与数据形状。修改契约先改本文。

## 1. 总体分层

```
┌──────────────────────────────────────────────────────────────┐
│  入口层                                                       │
│  ├─ MCP Server  (stdio)   gs_openapi.main / mcp-gs-robot      │
│  ├─ HTTP Server (FastAPI) gs_openapi.server / gs-robot-server │
│  │     ├─ REST  /api/v1/...                                   │
│  │     ├─ Agent SSE /api/v1/agent/...                         │
│  │     └─ H5 静态页 /  (由 h5/ 构建产物提供)                   │
│  ├─ 扫地僧 Saodi CLI      gs_openapi.agent.cli / saodi        │
│  └─ Skill                 skills/gs-robot/SKILL.md            │
├──────────────────────────────────────────────────────────────┤
│  工具注册表  gs_openapi.tools.registry  (单一真源)             │
│    ToolSpec(name, description, input_model, handler, dangerous)│
│    → MCP tool / Agent tool schema / REST handler 共用           │
├──────────────────────────────────────────────────────────────┤
│  扫地僧 Agent 核心  gs_openapi.agent.core (SaodiAgent)          │
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
| `SAODI_PROVIDER` | 否 | `anthropic`（默认）或 `openai` |
| `SAODI_MODEL` | 否 | 默认 anthropic→`claude-opus-5`；openai→`deepseek-chat` |
| `ANTHROPIC_API_KEY` | provider=anthropic 时 | Anthropic SDK 自动读取 |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | provider=openai 时 | 任意 OpenAI 兼容端点 |
| `SAODI_AUTO_APPROVE` | 否 | `1` 时危险操作不再二次确认 |
| `SAODI_MAX_TURNS` | 否 | 单轮对话最大工具循环次数，默认 12 |
| `SAODI_CONTEXT_DIR` | 否 | 私有经验目录：其下 `*.md`（按文件名排序）追加到系统提示末尾，供不开源的经验使用 |
| `SAODI_CONTEXT_MAX_CHARS` | 否 | 系统提示总长度上限（字符），默认 60000；超出时截断并记 WARNING |
| `SAODI_DATA_DIR` | 否 | 本地数据目录，默认 `~/.saodi/`；其下 `saodi.sqlite` 保存会话、工具调用日志与错误线程（§5.2），`memory.md` 是本地私有记忆（§5.3） |

兼容（保留一个版本，下个版本删除）：上表 `SAODI_PROVIDER` / `SAODI_MODEL` / `SAODI_AUTO_APPROVE` / `SAODI_MAX_TURNS` 读不到时回落旧名 `PI_AGENT_PROVIDER` / `PI_AGENT_MODEL` / `PI_AGENT_AUTO_APPROVE` / `PI_AGENT_MAX_TURNS`，每个旧名每进程打一次弃用 WARNING（只记变量名，不记值）。新旧同时设置时新名优先。

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
    local: bool = False            # True = 只读本地文件/参考表、不需要上游客户端（MCP 入口据此不建 GausiumV3）

REGISTRY: dict[str, ToolSpec]
def get_tool(name) -> ToolSpec
def list_tools(category: str | None = None) -> list[ToolSpec]
async def invoke(name: str, args: dict, v3: GausiumV3) -> Any   # 校验 + 调用，返回可 JSON 序列化对象
# 工具调用的唯一收口点：invoke 结束（成功或抛错）后通知观察者，观察者异常只记 WARNING、不影响调用结果
def add_call_observer(fn: Callable[[ToolCall], Awaitable[None] | None]) -> None   # 同一函数重复注册只算一次
def remove_call_observer(fn) -> None
def call_context(source: str, session_id: str | None = None)   # contextmanager，设置本次调用来源
# ToolCall: tool, args(原始入参), source(agent|rest|mcp|unknown), session_id, started_at, duration_ms, error(Exception|None)
def to_anthropic_tools() -> list[dict]     # {"name","description","input_schema"}
def to_openai_tools() -> list[dict]        # {"type":"function","function":{...}}
```

| 分类 | 工具名 | 输入（snake_case） | dangerous | V3 端点 |
|---|---|---|---|---|
| robots | `list_robots` | page=1, page_size=20, relation? | | legacy `GET v1alpha1/robots`（V3 无列表接口） |
| robots | `get_robot_status` | robot_sn_list: list[str] (≤100) | | robots/status/get；返回附加 `work_state_name`、`work_state_desc` |
| robots | `describe_work_state` | work_state: int | | 本地参考表（local） |
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
| reference | `lookup_error_code` | code: str（3–10 位数字，接受 int） | | 本地：检索 skill 的 `references/error-codes.md` 与 `references/experience.md`，返回 `{"code","found","matches":[{"source","section","text"}],"hint"?}`；表格行附表头；整数边界匹配（`30003` 不命中 `230003`），最多 10 条；未命中时 `hint` 要求如实报告、不要猜 |
| memory | `remember` | lesson: str, scope?: str | ✔ | 本地：向 `$SAODI_DATA_DIR/memory.md` 追加一行（§5.3），返回 `{"status":"added"\|"duplicate","entry","path"}`；空、超 500 字符或含密钥形态 → `ToolInputError` |

工具输入字段名一律 snake_case，`handler` 内部映射为文档的 camelCase。返回值统一为 `dict`/`list`（pydantic → `model_dump(by_alias=False)`），错误抛 `GausiumAPIError`，由各入口层转换。

## 4. HTTP Server（FastAPI）

- 启动：`gs-robot-server`（entry point）或 `uvicorn gs_openapi.server.app:app`。
- 前缀 `/api/v1`；所有响应 JSON；错误统一 `{"error": {"code": <int|str>, "message": str, "trace_id": str|null}}`。上游 `GausiumAPIError` → HTTP 502（code 为六位业务码），参数错误 → 422/400，鉴权失败 → 401。
- CORS：默认允许所有来源（H5 同源部署时无影响）。
- `GET /api/v1/health`（公开）→ `{"status":"ok","version":"0.3.0","agent_provider":"anthropic","tools":<int>,"auth_required":<bool>}`；`auth_required` 仅表示服务端是否设置了 `GS_SERVER_API_KEY`，绝不返回 key 本身
- `GET /api/v1/auth/check`（受 `X-API-Key` 保护、无副作用、不打上游）→ `{"ok":true}`；key 缺失或错误时 401。H5 设置页用它校验 key
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
- Agent（会话持久化在 SQLite，后端重启后可继续对话，见 §5.2）：
  - `POST /api/v1/agent/sessions` `{ "title"?: str }`（body 可省略）→ `{"session_id": str}`
  - `GET /api/v1/agent/sessions?page=1&page_size=20&include_empty=false` → `{"items":[{"session_id","title","created_at","updated_at","message_count"}],"total","page","page_size"}`，按 `updated_at` 倒序；默认不列出还没有消息的空会话
  - `GET /api/v1/agent/sessions/{id}` → `{"session_id","title","messages","errors","created_at","updated_at","message_count"}`。`messages` 为中立格式：`user` 的 `content` 是字符串或 `tool_result` 块数组（`tool_use_id`、`content`（JSON 文本）、`is_error`）；`assistant` 的 `content` 是块数组（`text`、`tool_use`（`id`、`name`、`input`），anthropic 还可能有 `thinking`）。`errors` 为本会话 SSE `error` 事件 `[{"message","at","after_message"}]`，`after_message` 是出错时 `messages` 的长度，用于把错误插回时间线
  - `DELETE /api/v1/agent/sessions/{id}` → `{"ok":true}`；会话运行中返回 409
  - `POST /api/v1/agent/sessions/{id}/messages` `{ "content": str }` → **SSE**（`text/event-stream`），每行 `data: <json>`，事件类型：
    - `{"type":"text_delta","text":str}`
    - `{"type":"tool_call","id":str,"name":str,"input":dict}`
    - `{"type":"tool_result","id":str,"name":str,"output":any,"is_error":bool}`
    - `{"type":"confirm_required","confirm_id":str,"name":str,"input":dict,"summary":str}` —— 流暂停，等待确认（最长 120s，超时视为拒绝）
    - `{"type":"done","message_id":str,"usage":{...}}`
    - `{"type":"error","message":str}`
  - `POST /api/v1/agent/sessions/{id}/confirm` `{ "confirm_id": str, "approve": bool }` → `{"ok": true}`
- 错误线程（受 `X-API-Key` 保护，见 §5.2）：
  - `GET /api/v1/errors/threads?status=&category=&limit=100` → `{"items":[Thread]}`，按 `last_seen` 倒序
  - `GET /api/v1/errors/threads/{id}` → `Thread` + `"calls":[Call]`（最近 20 次失败调用明细）+ `"tool_calls_total"`/`"tool_errors_total"`（该工具全部调用与失败次数，用于算失败率）；不存在 404
  - `PATCH /api/v1/errors/threads/{id}` `{ "status"?, "category"?, "note"? }` → 更新后的 `Thread`；取值非法 422
  - `Thread` = `{"id","fingerprint","tool","error_class","code","sample_msg","first_seen","last_seen","count","sn_count","trace_ids"(最近 5 条),"status","category","note","reopened_at"}`
  - `Call` = `{"id","ts","source","session_id","tool","args"(脱敏 JSON 文本),"robot_sn","duration_ms","status","http_status","code","msg","trace_id","endpoint","error_type","thread_id"}`
- 静态：`/`、`/index.html`、`/assets/*` 由 `src/gs_openapi/server/static/`（H5 构建产物）提供；目录不存在时 `/` 返回简短提示 JSON。

## 5. 扫地僧（Saodi）Agent 接口（供 server 与 CLI 调用）

`gs_openapi/agent/core.py`

```python
class AgentEvent(TypedDict): type: str; ...   # 与 SSE 事件同形
class ConfirmGate(Protocol):
    async def ask(self, session_id: str, confirm_id: str, name: str, input: dict, summary: str) -> bool: ...

class SaodiAgent:
    def __init__(self, v3: GausiumV3, provider: LLMProvider, *, auto_approve: bool = False, max_turns: int = 12, confirm_gate: ConfirmGate | None = None): ...
    async def run(self, session: AgentSession, user_text: str) -> AsyncIterator[AgentEvent]: ...

PiAgent = SaodiAgent  # 兼容别名，保留一个版本

class AgentSession:  # 内存态，可序列化
    session_id: str; messages: list[dict]; created_at: float
    system_prompt: str | None  # 会话首轮由 build_system_prompt() 生成并固定，不对外序列化
    title: str | None; updated_at: float
    errors: list[dict]         # SSE error 事件，见 §4 GET session
class SessionStore(Protocol):
    async def create(title=None) -> AgentSession
    async def get(session_id) -> AgentSession | None   # SQLite 实现每次返回新对象
    async def save(session) -> None                     # 每次 SSE 流结束（含断连/报错）都保存；无标题时取首条用户消息前 30 字
    async def delete(session_id) -> None
    async def list() -> list[AgentSession]              # 按 updated_at 倒序
    async def page(page, page_size, include_empty=False) -> tuple[list[dict], int]
# 默认 SqliteSessionStore（gs_openapi.store）；InMemorySessionStore 保留给测试
# 续聊前若历史以带 tool_use 的 assistant 结尾且无 tool_result（上次流中途断开），run() 先补一条
# user 消息，逐个 tool_use 追加 {type: tool_result, is_error: true, content: "上次执行被中断，结果未知"}

class LLMProvider(Protocol):
    async def stream(self, *, system: str, messages: list[dict], tools: list[dict]) -> AsyncIterator[ProviderEvent]: ...
    # ProviderEvent: text_delta | tool_use(id,name,input) | message_end(stop_reason, usage, assistant_content)
```

- `providers/anthropic.py`：`anthropic.AsyncAnthropic()`，`client.messages.stream(model, max_tokens=16000, system=[{type:text,text,cache_control:{type:ephemeral}}], tools=..., thinking={"type":"adaptive"}, messages=...)`；用 `stream.get_final_message()` 取完整 assistant content 回填历史；工具结果以一条 user 消息内多个 `tool_result` 返回。
- `providers/openai_compat.py`：`httpx` 调 `{OPENAI_BASE_URL}/chat/completions`（`stream=true`，`tools`），兼容 DeepSeek 等。
- 系统提示：见 §5.1，每个新会话生成一次并在该会话内固定（利于 prompt cache）。
- CLI：`saodi`（`gs_openapi/agent/cli.py`）：终端 REPL，`--provider/--model/--auto-approve/--robot`，危险操作在终端 y/N 确认；`saodi --show-context` 打印最终系统提示后退出（不需要 LLM key，不连上游）。`pi-agent` 为兼容别名，行为相同，启动时 stderr 打一行弃用提示。`saodi errors` 查看错误线程、`saodi errors promote <id>` 把线程提炼为本地记忆（§5.2）；`saodi memory` 管理本地记忆（§5.3）。CLI 会话不落库，但其工具调用照常记入调用日志。

### 5.1 认知上下文（Soul → Knowledge → Memory → 私有覆盖）

`gs_openapi/agent/prompts.py` 的 `build_system_prompt(*, context_dir=None, max_chars=None) -> str` 按固定顺序拼接：

| 层 | 来源 | 说明 |
|---|---|---|
| Soul | `gs_openapi/agent/soul.md`（包内，英文） | 身份（扫地僧 / Saodi）、语气（**按用户语言回复**，关键字段保留英文）、查错误码规则、何时提议 `remember`、安全底线 |
| Knowledge | `skills/gs-robot/`：`references/domain.md` → `SKILL.md`（去掉 YAML frontmatter）→ `references/work-states.md` | 与 Agent Skill **单一来源**，不复制。`references/error-codes.md`（约 23KB 官方码表）**不常驻**，由 `lookup_error_code` 按需检索 |
| Memory（开源） | `skills/gs-robot/references/experience.md` | 开源的通用调用经验；禁止写入 SN、traceId、账号、密钥、客户/站点名 |
| Memory（本地） | `$SAODI_DATA_DIR/memory.md`（标记 `<!-- memory: local memory.md -->`） | 可选，本机私有、不进 git；由 `remember` 工具 / `saodi memory` / `saodi errors promote` 写入（§5.3）；文件不存在时静默跳过 |
| 私有覆盖 | `$SAODI_CONTEXT_DIR/*.md`（按文件名排序） | 可选，不开源的经验 |

- skill 目录定位：先找包内 `gs_openapi/_skills/gs-robot/`（wheel 由 hatch `force-include` 从 `skills/gs-robot` 打入），找不到再用源码树 `skills/gs-robot/`（开发 / editable 安装）。两处都没有时 Knowledge / Memory 记 WARNING 后跳过。
- 总长度上限 `SAODI_CONTEXT_MAX_CHARS`（默认 60000 字符）：超限时**先**从本地 memory.md 删最旧的条目（`- [日期] …` 行，非条目行保留）直到放得下，WARNING 写明删了几条；仍超限（或没有本地记忆）时按顺序累加，越界的那个文件被截断、其后文件整体丢弃，WARNING 写明截断/丢弃了哪些文件。
- 日志只记加载了哪些文件与字节数，不记内容。

### 5.2 本地持久化（`gs_openapi.store`，stdlib `sqlite3`）

- 库文件 `$SAODI_DATA_DIR/saodi.sqlite`（默认 `~/.saodi/saodi.sqlite`），WAL + `synchronous=NORMAL` + `busy_timeout=5000`；所有读写经 `asyncio.to_thread`，不阻塞事件循环与 SSE。
- 表：`sessions`（id、title、system_prompt、messages JSON、errors JSON、message_count、created_at、updated_at）；`tool_calls`；`error_threads`；`error_thread_sns`（线程 × 去重 SN）。`PRAGMA user_version` 记 schema 版本。
- **工具调用日志**：HTTP Server、MCP stdio、`saodi` CLI 启动时各自注册同一个观察者（§3），因此 Agent 内调用、REST（`/tools/{name}` 与友好路由）、MCP 调用都在 `registry.invoke` 这一处记录。来源：Agent 在 `call_context("agent", session_id)` 内执行工具；HTTP 中间件设 `rest`；MCP 设 `mcp`。
  - 每次调用一行：时间、来源、session_id、tool、args（**递归脱敏**：键名含 `token/secret/key/password/authorization` 的值 → `***`，整体截 4KB）、robot_sn（从 `robot_sn`/`robot_sn_list` 提取）、耗时、`ok`/`error`、上游 HTTP 状态、上游业务 code、msg、traceId、endpoint、异常类型。成功也记（算失败率），**从不存响应体**。
  - 错误类别 `error_class`：`upstream`（`GausiumAPIError`）、`input`（`ToolInputError` / 未知工具）、`response_model`（handler 内 pydantic `ValidationError`，即上游响应与本地模型不一致）、`exception`（其余）。
- **错误线程**：失败调用按指纹归并。`fingerprint = tool | error_class | key`；key = 上游 code；无 code 时 = 异常类型 + 规范化 msg（`response_model` 取模型名，因为出错字段随返回数据变化、修复点是模型；入参校验错误取 `loc(下标→*):type` 集合；其余 msg 里的 uuid、长十六进制、SN、数字替换为占位符）。
  - 自动分类（仅新建线程时）：`110003` → `account_permission` + `expected`；`230003` → `robot_offline` + `expected`；`response_model` → `our_bug`；`input` → `input_error`；其余 `unknown`。未列出的新线程状态为 `open`。
  - 状态 `open | expected | fixed | wontfix`；分类 `our_bug | account_permission | robot_offline | upstream | input_error | unknown`；人工修改不会被自动分类覆盖。
  - **回归**：已标 `fixed` 的线程再次出现 → 自动改回 `open` 并写 `reopened_at`。
- 调用日志的 `args` 在键名脱敏之后，再对整段 JSON 文本做 `key=value` 形态的密钥掩码（自由文本入参里手敲的 `password=…` 也会变成 `***`）。
- CLI：`saodi errors [--status S] [--category C] [--json]` 打印线程表；`saodi errors show <id> [--json]` 打印线程与最近 20 次调用。只读本地库，不需要 LLM key，不连上游。
- `saodi errors promote <id>`：把线程提炼为一条本地记忆（scope `error-code`）。内容取线程 `note`；`note` 为空时用 `<tool> error <code|error_class> (<category>): <sample_msg>`（msg 里的 uuid / 长十六进制替换为 `<id>`）。成功后在 `note` 末尾追加 `[promoted to memory YYYY-MM-DD]`；已带该标记的线程拒绝重复提炼（退出码 1）；内容被密钥检查拒绝时退出码 1，提示先写一条干净的 note。只做人工触发，不自动提炼。

### 5.3 本地记忆（`gs_openapi.store.memory`）

- 文件 `$SAODI_DATA_DIR/memory.md`（目录 0700、文件 0600），首次写入时生成一行标题与说明。一行一条：`- [YYYY-MM-DD] lesson`（本地日期），新条目追加在末尾；带 scope 时为 `- [YYYY-MM-DD] <scope>: <lesson>`。多行输入压成一行，单条 ≤ 500 字符。
- 去重：与已有条目按「casefold + 空白归一 + 去掉末尾标点」比较，相同则返回 `duplicate`、不写。
- 拒绝密钥形态：`<含 token/secret/password/api_key/access_key/authorization 的键> [:=] 值`、`Bearer <串>`、`sk-/ak-/pk-/rk-` 前缀密钥、JWT、≥32 位字母数字混合长串（同时挡住 traceId / access token）。只是提到 token 一词（如 "token expires after 24h"）不拒绝。
- 写入入口：Agent 的 `remember`（dangerous，走确认流程；`SAODI_AUTO_APPROVE=1` 时免确认）、REST `POST /api/v1/tools/remember`（调用方即已确认）、MCP、`saodi memory add`、`saodi errors promote`。
- CLI：`saodi memory` 打印路径与内容；`saodi memory add "<lesson>" [--scope S]`；`saodi memory edit` 用 `$VISUAL` / `$EDITOR`（默认 `vi`）打开，文件不存在先创建。不需要 LLM key，不连上游。

## 6. H5（`h5/`，Vue 3 + Vite + TypeScript + Vant 4）

- 构建产物输出到 `src/gs_openapi/server/static/`（`vite.config.ts` 的 `build.outDir`，`base: './'`）。产物纳入 wheel（`pyproject` 的 `[tool.hatch.build.targets.wheel]` 不需改，因为在包目录内）。
- 页面（底部 Tabbar）：`/chat` 扫地僧聊天（SSE 流式、工具调用折叠卡片、confirm_required 弹确认按钮）、`/robots` 机器人列表（状态卡：在线、电量、工作状态名、当前地图）、`/robots/:sn` 详情（地图列表+画布图、能力、任务定义、快捷操作 开始/暂停/继续/停止/回充 带确认弹窗、最近报告）、`/settings`（API Base、API Key 保存到 localStorage）。
- 与后端通信：`fetch`；SSE 用 `fetch` + `ReadableStream` 逐行解析 `data:`。
- 开发：`npm run dev` 通过 Vite proxy 转发 `/api` 到 `http://127.0.0.1:8000`。

## 7. Skill（`skills/gs-robot/SKILL.md`）

Agent Skill（Claude Code / Codex / WorkBuddy 通用格式：YAML frontmatter `name`、`description` + 正文）。内容：何时使用、环境变量、通过 MCP 工具操作机器人的标准流程（查状态 → 查能力/资源 → 建任务定义 → 启动 → 轮询命令状态）、安全边界（危险工具需确认）、常见错误码处理、`references/` 里放工具速查表、工作状态表、领域模型（`domain.md`）与调用经验（`experience.md`）。同一目录同时是扫地僧 Agent 的 Knowledge / Memory 来源（§5.1），改这里即同时改两边。

## 8. 版本与兼容

- 版本 `0.3.0`（契约自 0.2.0 起向后兼容：新增工具、字段与 CLI 子命令，未删除任何接口）。V3 为默认工具集；旧版工具保留在 `gs_openapi/mcp/legacy_tools.py`，通过 `GS_ENABLE_LEGACY_TOOLS=1` 注册（名称加 `legacy_` 前缀），避免与 V3 工具名冲突。
- `python -m gs_openapi.main` / `mcp-gs-robot` 仍为 MCP stdio 入口。
- Agent 改名（Pi Agent → 扫地僧 / Saodi）的兼容层保留一个版本：`pi-agent` 命令、`PiAgent` 类别名、`PI_AGENT_*` 环境变量回落（见 §2、§5）。`GET /api/v1/health` 字段不变（`agent_provider` 语义不变）。
