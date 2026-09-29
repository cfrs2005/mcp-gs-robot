---
name: gs-robot
description: Operate and monitor Gausium cleaning robots (OpenAPI V3) through the mcp-gs-robot MCP tools — check status, inspect maps/resources, create and start combined tasks, manage schedules, navigate home, read task reports. Use when the user mentions Gausium/高仙 robots, robot serial numbers like GS…-…, cleaning tasks, or the mcp-gs-robot server.
---

# gs-robot — Agent Skill for operating Gausium robots

This skill teaches an AI assistant to operate Gausium cleaning robots through the `mcp-gs-robot` MCP tools (OpenAPI V3). Tool names match the registry in `ARCHITECTURE_V3.md §3`; inputs are always snake_case and the handlers map them to the documented camelCase.

## When to use

- The user mentions Gausium / 高仙 robots, or a robot serial number (robot_sn) shaped like `GS…-…` or `TEST00-0000-000-X014`.
- The user asks to: check status, look at maps/resources, create task definitions, start/pause/resume/stop tasks, plan schedules, send a robot home, read task reports.
- The user mentions the `mcp-gs-robot` server, the Saodi (扫地僧) agent, or this repository's MCP/HTTP entry points.

Not for: applying for an open-platform account or obtaining OAuth credentials (point the user to https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Quick%20Start).

## Prerequisites

### MCP configuration
The host (Claude Code / Codex / WorkBuddy) must mount the `mcp-gs-robot` MCP server (stdio entry `gs_openapi.main` / `mcp-gs-robot`). Once started, tools are registered by `name` and can be called directly. The REST / agent SSE entry is `gs-robot-server` (`/api/v1/...`); this skill uses MCP tool calls by default.

### Environment variables (ARCHITECTURE_V3.md §2)
| Variable | Required | Description |
|---|---|---|
| `GS_CLIENT_ID` / `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` | yes | Open-platform credentials (the AccessKeySecret goes into `GS_OPEN_ACCESS_KEY`) |
| `GS_BASE_URL` | no | Default `https://openapi.gs-robot.com/` |
| `GS_HTTP_TIMEOUT` | no | Seconds, default 30 |
| `GS_SERVER_API_KEY` | no | When set, the HTTP server checks `X-API-Key` |
| `SAODI_AUTO_APPROVE` | no | `1` skips the second confirmation for dangerous tools (confirmation is on by default) |

Tokens are refreshed automatically by `gs_openapi.auth.token_manager`; callers never refresh by hand.

## Standard workflow

Core order: **status → capabilities → resources → task definition → start → poll the command status**. Each step lists the tool and its key parameters; dangerous tools (dangerous ✔) follow the safety rules in the next section.

### 1. Robot status
- `list_robots` (page=1, page_size=20) → the robot_sn list (legacy `GET v1alpha1/robots`; V3 has no list endpoint).
- `get_robot_status` (robot_sn_list: ["<SN>", ...], ≤100) → `workState`, `onlineStatus`, `batteryPercent`, `currentMapName`, …, plus `work_state_name` / `work_state_desc`.
- Look up a state code with `describe_work_state` (work_state: <int>) or in `references/work-states.md`.
- Note: snapshots are not real time (up to ~30 s lag); runtime fields such as battery, map and position may be empty for offline robots.

### 2. Capabilities and work modes
- `get_robot_capabilities` (robot_sn) → the combined-task capabilities of the robot (`tasks/fusion/robot-capabilities/get`).
- `list_work_modes` (robot_sn) → work modes (mode/subType/type/configType/strengthOptions). See https://developer.gs-robot.com/v3docs/en_US/Task%20Work%20Mode%20Reference.

### 3. Maps and task resources
- `list_robot_maps` (robot_sn) → maps; take `map_id`.
- `get_map_canvas` (robot_sn, map_id) → the map canvas image (`robots/maps/canvas/get`).
- `list_charging_positions` (robot_sn, map_id?) → charging positions (`maps/charging-positions/list`).
- `list_map_resources` (robot_sn, map_id_list) → map resources without work_modes (`maps/map-resources/list`).
- `list_task_resources` (robot_sn, map_id_list, include_paths=True, include_regions=True, include_positions=False) → **always query before creating tasks/schedules**; returns `workModes` + `maps` (regions/paths/positions with their `mapResourceId`, `mapResourceType`, `supportedActions`). Source endpoint `maps/schedule-resources/list`.

### 4. Create a task definition (dangerous ✔)
- `create_task_definition` (robot_sn, task_name, work_mode: dict, map_resource_list: list[dict], loop_count?, site_id?, task_advance_config?) → success only; internal fields are not echoed. Endpoint `tasks/persistence/create`.
  - `work_mode` needs at least `mode`; omit `strength` for the default level; fixed-configuration modes (inspect/strong_wash) do not accept `strength`.
  - Each `map_resource_list` item needs at least `map_id` + `map_resource_id` + `map_resource_type` (region/path/position).
- Manage them with `list_task_definitions` / `get_task_definition` / `update_task_definition` / `delete_task_definition`.

### 5. Start a task (dangerous ✔)
- `start_task` (robot_sn, fusion_task_id, loop_count?) → endpoint `robots/commands/tasks/start`. Returns `data.requestId`, `cmdStatus`, `taskInstanceId`.
- While running: `pause_task` / `resume_task` / `stop_task` / `skip_task_item` (all dangerous ✔, parameter robot_sn).

### 6. Poll the command status
- `get_command_status` (robot_sn, request_id) → `cmdStatus`, `cmdResultCode`, `commandType`. Endpoint `robots/commands/status/get`.
- `list_command_history` (robot_sn, page=1, pagesize=20) → history page.
- Convenience: `wait_for_command` (robot_sn, request_id, timeout_seconds=60) polls until a terminal state.
- Combined: `run_cleaning_task` (robot_sn, task_name, map_id, resource_ids, mode="sweep", strength?, loop_count=1, wait_seconds=30) → runs capabilities→task_resources→create_task_definition→start_task→poll.

### 7. Schedules (dangerous ✔)
- Simple schedules: `create_simple_schedule` / `update_simple_schedule` / `delete_simple_schedule` (+ plan_uuid). Endpoints `schedules/plans/simple/{create,update,delete}`.
- Standard schedules: `create_schedule` / `update_schedule` / `delete_schedule` / `list_schedules` / `get_schedule`.
- Queries: `get_schedule_calendar` (robot_sn, year_month), `list_schedule_pre_tasks` (robot_sn, date).
- Key simple-schedule fields: `plan_execute_type` (1=timed TIMED_SCHEDULING_TASK / 2=quantitative QUANTITATIVE_SCH_TASK), `plan_repeat_type` (0=once / 2=weekly), `plan_repeat_weekly` (0-6 = Sunday…Saturday), `plan_start_date` yyyy-MM-dd, `plan_start_time` HH:mm 24h, `site_mode` (0=whole area, no site_id / 1=specific site, site_id required). Each `map_resource_list` item only needs `map_id` + `map_resource_id` + `map_resource_type` (region/path).

### 8. Navigation and reports
- `navigate_home` (robot_sn, …) dangerous ✔ → `robots/commands/navigation/go-home`; with `pause_navigation` / `resume_navigation` / `stop_navigation` (all dangerous ✔).
- `list_task_reports` (robot_sn, page=1, pagesize=20, end_time_min?, end_time_max?) → `taskreports/page`.
- `get_task_report_map_images` (documented fields) → `taskreports/map-images/query`.

### 9. Reference and memory (local, no upstream call)
- `lookup_error_code` (code) → matching rows from `references/error-codes.md` and entries in `references/experience.md`. Use it for any code you do not recognise; do not guess.
- `remember` (lesson, scope?) dangerous ✔ → appends one verified, reusable lesson to the local memory file `$SAODI_DATA_DIR/memory.md` (`- [YYYY-MM-DD] lesson`, de-duplicated, credential-looking text refused).

## Safety rules

1. **Restate and confirm before any dangerous tool**: before calling a tool marked dangerous ✔ in §3 (create/update/delete_task_definition, start_task/pause_task/resume_task/stop_task/skip_task_item, schedule create/update/delete, navigate_home and navigation control, run_cleaning_task, remember), restate "I will run <action> on robot <SN> with <key fields>" and wait for clear consent. With `SAODI_AUTO_APPROVE=1` confirmation may be skipped, but still say in the output what was executed.
2. **Status snapshots lag ≤30 s**: `workState`, battery, position etc. from `get_robot_status` are not real time; runtime fields of offline robots may be empty, so never conclude from them that the robot is "at its origin" or "has no task".
3. **cmdStatus=6 only means delivered**: asynchronous commands such as `start_task` return `cmdStatus=6` (`cmdResultCode=6880`) when the command reached the robot — **not that the robot started executing**. Track to a terminal state with `get_command_status` or `wait_for_command`, or confirm the workState change with `get_robot_status`.
4. **Credential safety**: never print `GS_CLIENT_SECRET` / `GS_OPEN_ACCESS_KEY` in plain text; when debugging show only the first 4 characters + `***`.
5. **Query resources before creating tasks**: `work_mode` and `map_resource_list` must come from a real `list_task_resources` response; never make up IDs from memory.

## Handling common errors

- **Business error codes**: a business response has `code != 0` and a descriptive `msg`. Platform business codes have six digits (e.g. 110003, 230003; handling in `references/experience.md`); robot task codes have ten digits (e.g. 2010100007). Task-start failure codes are in `references/error-codes.md` (source: the official Task Startup Failure Error Codes page); look them up with `lookup_error_code`. Frequent ones:
  - `2010100007` task area unreachable → check the map resources are still valid and the robot is online.
  - `2010100017` duplicate task name → choose another name or delete the old definition first.
  - `2010100018` version conflict, robot data has been updated → query `list_task_resources` again and recreate.
  - `2020100003` map not found by ID → check where the `map_id` came from.
  - `2050104001` another operation is in progress → retry later.
  - `2100101001` robot lost its localisation → ask the user to check the robot's position on site / remap.
- **401 authentication failure**: the token expired; `token_manager` refreshes it with the refresh_token automatically. If the refresh also fails, ask the user to check `GS_CLIENT_ID/SECRET/OPEN_ACCESS_KEY`.
- **422/400 parameter errors**: check required fields, snake_case spelling and `map_resource_type` values (region/path/position).
- **Task-start failure code table**: full list in `references/error-codes.md` and https://developer.gs-robot.com/v3docs/en_US/OpenAPI%20V3/Task%20Startup%20Failure%20Error%20Codes.

## Output conventions

- Reply in the user's language; keep key terms in English (workState, fusion_task_id, cmdStatus, …).
- Several robots' status as a table: `robot_sn | online | workState (name) | battery | current map | task`.
- Before a tool call, say its purpose in one sentence; before a dangerous tool, always restate and confirm.
- Error codes as: `<code> <msg> → <next action>`.
- Never print real credentials; use placeholders for SNs and IDs in examples.

## Reference files
- `references/tools.md` — quick reference of all tools (name / purpose / required parameters / dangerous / V3 endpoint).
- `references/work-states.md` — workState code table + operational meaning / next actions.
- `references/error-codes.md` — task-start failure codes + common HTTP/OAuth errors (official table, kept verbatim).
- `references/workflows.md` — 3 end-to-end example conversations.
- `references/domain.md` — domain model: cleaning robot basics, how robots/maps/resources/tasks/schedules/commands relate, error-code layers.
- `references/experience.md` — field-tested call experience (open source; no SN/traceId/account/secret/customer site names).
- The Saodi (扫地僧) agent loads `domain.md`, this file, `work-states.md` and `experience.md` as the system prompt of every session (see `docs/ARCHITECTURE_V3.md` §5.1); `error-codes.md` is looked up on demand with `lookup_error_code`. Editing these files changes both the skill and the agent.
- Sources: `docs/ARCHITECTURE_V3.md` (contract) and the official Gausium OpenAPI V3 documentation (endpoint reference, indexed in `docs/apis.md`).
