# Domain model: commercial cleaning robots and OpenAPI V3

The minimum conceptual model needed to understand the V3 interfaces. Tool order is in `SKILL.md`, state codes in `work-states.md`, error codes in `error-codes.md` (Saodi looks them up with `lookup_error_code`), and field-tested pitfalls in `experience.md`. What a specific model can do is always decided by the API responses; this file does not replace the official documentation.

## 1. Commercial cleaning robot basics

- **Job types**: Gausium commercial cleaning robots serve large public spaces such as malls, office buildings, airports and factories. Common job types are scrubbing (scrub + squeegee pick-up), sweeping / dust-pushing and vacuuming; some models support several. **What a given robot can do comes from `get_robot_capabilities` and `list_work_modes`; never guess from the model name.**
- **Prerequisite for autonomy**: the robot must first map the site (scan the map, record regions / paths) before it can run tasks on that map. Do not interrupt mapping or map saving (workState 150/160/250 and similar).
- **Supplies and charging**: jobs consume battery, clean water and dust-bag / dirty-water capacity. Low battery enters low-battery mode (workState 360–390); the robot can go home to charge (`navigate_home`, back to the charging position). Some models pair with a workstation for automatic water filling and draining (workState 200/300/310).
- **Site factors**: multi-floor jobs involve elevators (workState 260/320/330/340), passages may involve gates (430–432). Emergency stop, collisions and lost localisation are on-site problems; remotely you can only report them truthfully, not "fix" them.
- **Firmware generations**: the official documentation marks each endpoint's supported versions (all AIO versions / A5+ / A6+). Map endpoints are mostly A5+; task definitions, schedules and work modes are mostly A6+. Calling a newer endpoint on old firmware may fail; that is an unsupported capability, not a parameter error. See `docs/apis.md` in the repository for the endpoint/version table.

## 2. Object relationships

```
robot robot_sn
 ├─ status snapshot: onlineStatus, workState, battery, current map… (not real time, ~30 s lag)
 ├─ capabilities / work modes: mode, subType, type, configType, strengthOptions
 ├─ map (map_id; list items may only carry robotMapUuid / mapVersionId / displayName)
 │    └─ map resource: mapResourceId + mapResourceType (region / path / position)
 │         └─ supportedActions: which jobs the resource supports
 ├─ task definition (persistent combined task, fusion_task_id)
 │    = task_name + work_mode + map_resource_list[{map_id, map_resource_id, map_resource_type}] + loop_count
 ├─ schedule plan (plan_uuid) → the platform generates pre-tasks when due
 ├─ command (request_id): cmdStatus, cmdResultCode, commandType
 │    └─ start commands create a task instance taskInstanceId
 └─ task report: produced after a task ends; its map trajectory image can be queried
```

## 3. Work modes

- `list_work_modes` returns the modes available on the robot. Key fields: `mode` (e.g. `sweep`), `subType`, `type`, `configType`, `strengthOptions` (selectable strength levels).
- A task's `work_mode` needs at least `mode`; `strength` must be one of `strengthOptions`, and the default level is used when omitted. Fixed-configuration modes (such as `inspect`, `strong_wash`) do not accept `strength`.
- Modes and resources must match: a mode not in the resource's `supportedActions` fails at start with an error such as "Task area does not support the current job type" (2010100008).
- See the official Task Work Mode Reference for the list of modes.

## 4. Maps, regions and resources

- A **map** is the product of one mapping run; a robot can have several maps, and tasks can only use maps that exist on the robot.
- **Resources** hang off a map: a region is a cleanable area, a path is a recorded route, a position is a point (such as the charging position, `list_charging_positions`).
- `list_map_resources`: map resources only; `list_task_resources`: resources plus usable work modes — **it is the source of truth before creating tasks and schedules**.
- Resource IDs are bound to a map version. After a map is rebuilt or updated, old IDs may become invalid, showing up as 2010100018 (version conflict), 2020100003 (map not found) or 2010100007 (area unreachable). Query the resources again; do not reuse old IDs.

## 5. Tasks and scheduling

- **Task definition** (persistent combined task): created with `create_task_definition`, then queried / updated / deleted by `fusion_task_id`; `task_name` must be unique per robot (2010100017).
- **Start**: `start_task(robot_sn, fusion_task_id, loop_count?)` sends the start command and returns `requestId`, `cmdStatus`, `taskInstanceId`. While running you can pause / resume / stop / skip (skip the current sub-item).
- **Schedules**:
  - Simple schedule: timed / quantitative × once / weekly; field values are in `SKILL.md` §7.
  - Standard schedule: a fuller plan model, plus the month calendar `get_schedule_calendar` and the daily pre-tasks `list_schedule_pre_tasks`.
  - Common constraints: one cleaning run ≤ 8 hours, start time not in the past, at least 1 minute from adjacent tasks (2010105001–2010105006).
- Temporary tasks and scheduled tasks have priorities; conflicts report 2010100012 / 2010100016.

## 6. Commands and state

- Every control endpoint (task start/stop, navigation) is an **asynchronous command**: the response means the command was accepted; track the outcome with `get_command_status(robot_sn, request_id)` or poll with `wait_for_command`.
- `cmdStatus=6` (often with `cmdResultCode=6880`) = the command reached the robot. **It does not mean execution started, let alone that the task finished.** Execution has started when workState enters 230 (AUTO_TASKING); it has finished when workState returns to idle and a task report appears.
- `wait_for_command` treats cmdStatus 0/1/2 as in progress and returns on 6 or on any other status that carries a result code.
- `commandType` values: START_FUSION_TASK, PAUSE_TASK, RESUME_TASK, STOP_TASK, SKIP_TASK, CROSS_NAVIGATE (go home), PAUSE_NAVIGATE, RESUME_NAVIGATE, STOP_NAVIGATE.
- "Ready for a task" means: `onlineStatus` online + workState=100 (IDLE) + enough battery.

## 7. The layers of error codes

| Layer | Shape | Examples | Meaning |
|---|---|---|---|
| Open-platform business code | six digits | 110003, 230003 | Platform / gateway side: credentials, binding, routing to the robot failed, etc.; see `experience.md` |
| Robot task code | ten digits, starting with 20… | 2010100007, 2100101001 | Why the robot refused to execute; see `error-codes.md` |
| HTTP status | 401 / 422 / 429 / 502 … | — | This repository's HTTP server turns upstream business errors into 502, with one of the codes above in `error.code` |

On business errors the upstream usually still answers HTTP 200; `code != 0` in the body tells them apart, `msg` is an English description, and `traceId` is for the platform's own investigation (tell the user only when needed; never write it into any experience file).
