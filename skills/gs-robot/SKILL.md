---
name: gs-robot
description: Operate and monitor Gausium cleaning robots (OpenAPI V3) through the mcp-gs-robot MCP tools — check status, inspect maps/resources, create and start combined tasks, manage schedules, navigate home, read task reports. Use when the user mentions Gausium/高仙 robots, robot serial numbers like GS…-…, cleaning tasks, or the mcp-gs-robot server.
---

# gs-robot — Gausium 机器人运维 Agent Skill

本 Skill 教会 AI 助手通过 `mcp-gs-robot` MCP 工具（OpenAPI V3）运维高仙（Gausium）清洁机器人。工具名与 `ARCHITECTURE_V3.md §3` 注册表一致；输入字段一律 snake_case，handler 内部映射为文档的 camelCase。

## 何时使用

- 用户提到高仙 / Gausium 机器人、形如 `GS…-…` 或 `TEST00-0000-000-S014` 的机器人序列号（robot_sn）。
- 用户要求：查状态、看地图/资源、建任务定义、启动/暂停/继续/停止任务、排班计划、回充导航、读任务报告。
- 用户提到 `mcp-gs-robot` 服务、Pi Agent、或本仓库的 MCP/HTTP 入口。

不适用：仅查询开放平台账号申请、OAuth 凭据获取流程（引导用户看 https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Quick%20Start）。

## 前置条件

### MCP 配置
宿主（Claude Code / Codex / WorkBuddy）需挂载 `mcp-gs-robot` MCP server（stdio 入口 `gs_openapi.main` / `mcp-gs-robot`）。启动后工具以 `name` 注册，可直接调用。REST / Agent SSE 入口为 `gs-robot-server`（`/api/v1/...`），本 Skill 默认走 MCP 工具调用。

### 环境变量（ARCHITECTURE_V3.md §2）
| 变量 | 必填 | 说明 |
|---|---|---|
| `GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` | 是 | 开放平台凭据（AccessKeySecret 作 `GS_OPEN_ACCESS_KEY`） |
| `GS_BASE_URL` | 否 | 默认 `https://openapi.gs-robot.com/` |
| `GS_HTTP_TIMEOUT` | 否 | 秒，默认 30 |
| `GS_SERVER_API_KEY` | 否 | 设则 HTTP Server 校验 `X-API-Key` |
| `PI_AGENT_AUTO_APPROVE` | 否 | `1` 时危险操作免二次确认（默认需确认） |

token 自动刷新由 `gs_openapi.auth.token_manager` 处理；调用方无需手动 refresh。

## 标准工作流

核心顺序：**状态 → 能力 → 资源 → 任务定义 → 启动 → 轮询命令状态**。每一步都给出工具名与关键参数；危险工具（dangerous ✔）见下一节安全规则。

### 1. 查机器人状态
- `list_robots`（page=1, page_size=20）→ 拿到 robot_sn 列表（legacy `GET v1alpha1/robots`，V3 无列表接口）。
- `get_robot_status`（robot_sn_list: ["<SN>", ...]，≤100）→ 返回 `workState`、`onlineStatus`、`batteryPercent`、`currentMapName` 等，附带 `work_state_name` / `work_state_desc`。
- 状态码含义用 `describe_work_state`（work_state: <int>）查本地参考表，或见 `references/work-states.md`。
- 注意：状态快照非实时，最大延迟约 30s；离线机器人的电量/地图/位置等运行时字段可能为空。

### 2. 查能力与工作模式
- `get_robot_capabilities`（robot_sn）→ 该机器人支持的组合任务能力（`tasks/fusion/robot-capabilities/get`）。
- `list_work_modes`（robot_sn）→ 工作模式列表（mode/subType/type/configType/strengthOptions）。详见 https://developer.gs-robot.com/v3docs/en_US/Task%20Work%20Mode%20Reference。

### 3. 查地图与任务资源
- `list_robot_maps`（robot_sn）→ 地图列表，拿 `map_id`。
- `get_map_canvas`（robot_sn, map_id）→ 地图画布图（`robots/maps/canvas/get`）。
- `list_charging_positions`（robot_sn, map_id?）→ 充电桩位（`maps/charging-positions/list`）。
- `list_map_resources`（robot_sn, map_id_list）→ 不含 work_modes 的纯地图资源（`maps/map-resources/list`）。
- `list_task_resources`（robot_sn, map_id_list, include_paths=True, include_regions=True, include_positions=False）→ **建任务/排班前必查**，返回 `workModes` + `maps`（regions/paths/positions 与各自的 `mapResourceId`、`mapResourceType`、`supportedActions`）。来源端点 `maps/schedule-resources/list`。

### 4. 建任务定义（dangerous ✔）
- `create_task_definition`（robot_sn, task_name, work_mode: dict, map_resource_list: list[dict], loop_count?, site_id?, task_advance_config?）→ 返回成功即可，内部字段不回显。端点 `tasks/persistence/create`。
  - `work_mode` 至少含 `mode`；`strength` 省略用默认档；固定配置模式（inspect/strong_wash）不接受 `strength`。
  - `map_resource_list` 每项至少 `map_id` + `map_resource_id` + `map_resource_type`（region/path/position）。
- 可用 `list_task_definitions` / `get_task_definition` / `update_task_definition` / `delete_task_definition` 管理。

### 5. 启动任务（dangerous ✔）
- `start_task`（robot_sn, fusion_task_id, loop_count?）→ 端点 `robots/commands/tasks/start`。返回 `data.requestId`、`cmdStatus`、`taskInstanceId`。
- 运行中控制：`pause_task` / `resume_task` / `stop_task` / `skip_task_item`（均 dangerous ✔，参数 robot_sn）。

### 6. 轮询命令状态
- `get_command_status`（robot_sn, request_id）→ `cmdStatus`、`cmdResultCode`、`commandType`。端点 `robots/commands/status/get`。
- `list_command_history`（robot_sn, page=1, pagesize=20）→ 历史记录页。
- 便捷封装：`wait_for_command`（robot_sn, request_id, timeout_seconds=60）轮询至终态。
- 组合封装：`run_cleaning_task`（robot_sn, task_name, map_id, resource_ids, mode="sweep", strength?, loop_count=1, wait_seconds=30）→ 自动跑 capabilities→task_resources→create_task_definition→start_task→轮询。

### 7. 排班计划（dangerous ✔）
- 简易排班：`create_simple_schedule` / `update_simple_schedule` / `delete_simple_schedule`（+ plan_uuid）。端点 `schedules/plans/simple/{create,update,delete}`。
- 标准排班：`create_schedule` / `update_schedule` / `delete_schedule` / `list_schedules` / `get_schedule`。
- 查询：`get_schedule_calendar`（robot_sn, year_month）、`list_schedule_pre_tasks`（robot_sn, date）。
- 简易排班关键字段：`plan_execute_type`（1=定时 TIMED_SCHEDULING_TASK / 2=定量 QUANTITATIVE_SCH_TASK）、`plan_repeat_type`（0=单次 / 2=每周）、`plan_repeat_weekly`（0-6=周日…周六）、`plan_start_date` yyyy-MM-dd、`plan_start_time` HH:mm 24h、`site_mode`（0=全区禁 site_id / 1=指定 site_id 必填）。`map_resource_list` 每项只需 `map_id` + `map_resource_id` + `map_resource_type`（region/path）。

### 8. 导航与报告
- `navigate_home`（robot_sn, …）dangerous ✔ → `robots/commands/navigation/go-home`；配套 `pause_navigation` / `resume_navigation` / `stop_navigation`（均 dangerous ✔）。
- `list_task_reports`（robot_sn, page=1, pagesize=20, end_time_min?, end_time_max?）→ `taskreports/page`。
- `get_task_report_map_images`（按文档字段）→ `taskreports/map-images/query`。

## 安全规则

1. **dangerous 工具必须先复述并确认**：凡 §3 标记 dangerous ✔ 的工具（create/update/delete_task_definition、start_task/pause_task/resume_task/stop_task/skip_task_item、schedule 增改删、navigate_home 及导航控制、run_cleaning_task），调用前必须向用户复述「将对机器人 <SN> 执行 <动作>，参数 <关键字段>」并等待明确同意；`PI_AGENT_AUTO_APPROVE=1` 时可免确认，但仍应在输出中说明已执行。
2. **状态快照≤30s 延迟**：`get_robot_status` 的 `workState`、电量、位置等非实时；离线机器人运行时字段可能为空，不得据此判定机器人「在原点」或「无任务」。
3. **cmdStatus=6 仅代表下发成功**：`start_task` 等异步命令返回 `cmdStatus=6`（`cmdResultCode=6880`）只表示命令已下发，**不代表机器人已开始执行**。需用 `get_command_status` 或 `wait_for_command` 跟踪到终态，或用 `get_robot_status` 看 `workState` 变化确认。
4. **凭据安全**：不得在对话中输出 `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` 明文；调试时只显示前 4 位 + `***`。
5. **建任务前必查资源**：`work_mode` 与 `map_resource_list` 必须来自 `list_task_resources` 的真实返回，不得凭记忆编造 ID。

## 常见错误处理

- **六位错误码**：业务响应 `code != 0` 为六位错误码，`msg` 为描述。任务启动失败码见 `references/error-codes.md`（源 `task-startup-failure-error-codes.md`）。常见高频：
  - `2010100007` 任务区域不可达 → 检查地图资源是否仍有效、机器人是否在线。
  - `2010100017` 任务名重复 → 换名或先删旧定义。
  - `2010100018` 版本冲突，机器人数据已更新 → 重新查 `list_task_resources` 再建。
  - `2020100003` 按 ID 找不到地图 → 核对 `map_id` 来源。
  - `2050104001` 有其他操作进行中 → 稍后重试。
  - `2100101001` 机器人丢失定位 → 提示用户确认机器人位置/重新建图。
- **401 鉴权失败**：token 过期，由 `token_manager` 自动用 refresh_token 刷新；若 refresh 也失败，提示用户检查 `GS_CLIENT_ID/SECRET/OPEN_ACCESS_KEY`。
- **422/400 参数错误**：检查必填字段、snake_case 拼写、`map_resource_type` 取值（region/path/position）。
- **任务启动失败码表**：完整列表见 `references/error-codes.md` 与 https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Task%20Startup%20Failure%20Error%20Codes。

## 输出规范

- 简洁中文为主，关键术语保留英文（workState、fusion_task_id、cmdStatus 等）。
- 多机器人状态用表格展示：`robot_sn | online | workState(名) | 电量 | 当前地图 | 任务`。
- 工具调用前用一句话说明意图；危险工具调用前必须复述确认。
- 错误码输出格式：`<六位码> <msg> → <建议动作>`。
- 不输出真实凭据；SN 与 ID 在示例中用占位符。

## 参考文件索引
- `references/tools.md` — 全工具速查表（名称/用途/必填参数/dangerous/V3 端点）。
- `references/work-states.md` — workState 码表 + 运维含义/建议动作。
- `references/error-codes.md` — 任务启动失败错误码 + 常见 HTTP/OAuth 错误。
- `references/workflows.md` — 3 个端到端示例对话脚本。
- 源文档：`docs/ARCHITECTURE_V3.md`（契约）、高仙 OpenAPI V3 官方文档（端点参考，索引见 `docs/apis.md`）。
