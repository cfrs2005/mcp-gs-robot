# 工具速查表

来源：`docs/ARCHITECTURE_V3.md §3` 工具注册表。输入字段一律 snake_case，handler 内部映射为文档 camelCase。dangerous ✔ 的工具调用前必须向用户复述并确认。

## robots
| 工具名 | 用途 | 必填参数 | dangerous | V3 端点 |
|---|---|---|---|---|
| `list_robots` | 分页列出机器人（拿 robot_sn） | page=1, page_size=20, relation? | | legacy `GET v1alpha1/robots`（V3 无列表接口） |
| `get_robot_status` | 批量状态快照（≤100），附 work_state_name/desc | robot_sn_list: list[str] | | `robots/status/get` |
| `describe_work_state` | 查 workState 本地参考表 | work_state: int | | 本地参考表（无端点） |
| `get_robot_capabilities` | 机器人组合任务能力 | robot_sn | | `tasks/fusion/robot-capabilities/get` |

## maps
| 工具名 | 用途 | 必填参数 | dangerous | V3 端点 |
|---|---|---|---|---|
| `list_robot_maps` | 列机器人地图，拿 map_id | robot_sn | | `robots/maps/list` |
| `get_map_canvas` | 取地图画布图 | robot_sn, map_id | | `robots/maps/canvas/get` |
| `list_charging_positions` | 列充电桩位 | robot_sn, map_id? | | `maps/charging-positions/list` |
| `list_map_resources` | 纯地图资源（不含 work_modes） | robot_sn, map_id_list | | `maps/map-resources/list` |
| `list_task_resources` | 建任务/排班前必查：workModes + regions/paths/positions | robot_sn, map_id_list, include_paths=True, include_regions=True, include_positions=False | | `maps/schedule-resources/list` |

## tasks
| 工具名 | 用途 | 必填参数 | dangerous | V3 端点 |
|---|---|---|---|---|
| `list_work_modes` | 列工作模式（mode/subType/type/strengthOptions） | robot_sn | | `tasks/fusion/work-modes/list` |
| `list_task_definitions` | 分页列任务定义 | robot_sn, page=1, pagesize=20 | | `tasks/persistence/page` |
| `get_task_definition` | 取单个任务定义 | robot_sn, fusion_task_id | | `tasks/persistence/get` |
| `create_task_definition` | 建组合任务定义 | robot_sn, task_name, work_mode: dict, map_resource_list: list[dict], loop_count?, site_id?, task_advance_config? | ✔ | `tasks/persistence/create` |
| `update_task_definition` | 改任务定义 | 同 create + fusion_task_id | ✔ | `tasks/persistence/update` |
| `delete_task_definition` | 删任务定义 | robot_sn, fusion_task_id | ✔ | `tasks/persistence/delete` |
| `start_task` | 启动任务（异步，返回 requestId） | robot_sn, fusion_task_id, loop_count? | ✔ | `robots/commands/tasks/start` |
| `pause_task` | 暂停当前任务 | robot_sn | ✔ | `robots/commands/tasks/pause` |
| `resume_task` | 恢复当前任务 | robot_sn | ✔ | `robots/commands/tasks/resume` |
| `stop_task` | 停止当前任务 | robot_sn | ✔ | `robots/commands/tasks/stop` |
| `skip_task_item` | 跳过当前任务项 | robot_sn | ✔ | `robots/commands/tasks/skip` |

## schedules
| 工具名 | 用途 | 必填参数 | dangerous | V3 端点 |
|---|---|---|---|---|
| `create_simple_schedule` | 建简易排班 | robot_sn, task_name, work_mode, map_resource_list, plan_execute_type, plan_repeat_type, plan_start_date, plan_start_time, site_mode（+ plan_repeat_weekly 若每周 / plan_stop_time 若定时 / site_id 若 site_mode=1） | ✔ | `schedules/plans/simple/create` |
| `update_simple_schedule` | 改简易排班 | 同 create + plan_uuid | ✔ | `schedules/plans/simple/update` |
| `delete_simple_schedule` | 删简易排班 | robot_sn, plan_uuid | ✔ | `schedules/plans/simple/delete` |
| `create_schedule` | 建标准排班 | 按标准 schedule 文档字段 | ✔ | `schedules/plans/create` |
| `update_schedule` | 改标准排班 | + plan 标识 | ✔ | `schedules/plans/update` |
| `delete_schedule` | 删标准排班 | robot_sn, plan id | ✔ | `schedules/plans/delete` |
| `list_schedules` | 列排班 | robot_sn, page… | | `schedules/plans/list` |
| `get_schedule` | 取排班详情 | robot_sn, plan id | | `schedules/plans/get` |
| `get_schedule_calendar` | 按月查排班日历 | robot_sn, year_month | | `schedules/plans/calendar/month/get` |
| `list_schedule_pre_tasks` | 按日查预排任务 | robot_sn, date | | `schedules/plans/pre-tasks/day/list` |

## commands
| 工具名 | 用途 | 必填参数 | dangerous | V3 端点 |
|---|---|---|---|---|
| `get_command_status` | 查命令下发/执行状态 | robot_sn, request_id | | `robots/commands/status/get` |
| `list_command_history` | 分页列命令历史 | robot_sn, page=1, pagesize=20 | | `robots/commands/status/page` |
| `navigate_home` | 回充导航 | robot_sn（+ 文档其它字段） | ✔ | `robots/commands/navigation/go-home` |
| `pause_navigation` | 暂停导航 | robot_sn | ✔ | `robots/commands/navigation/pause` |
| `resume_navigation` | 恢复导航 | robot_sn | ✔ | `robots/commands/navigation/resume` |
| `stop_navigation` | 停止导航 | robot_sn | ✔ | `robots/commands/navigation/stop` |

## reports
| 工具名 | 用途 | 必填参数 | dangerous | V3 端点 |
|---|---|---|---|---|
| `list_task_reports` | 分页列任务报告 | robot_sn, page=1, pagesize=20, end_time_min?, end_time_max? | | `taskreports/page` |
| `get_task_report_map_images` | 查报告地图图片 | 按文档字段 | | `taskreports/map-images/query` |

## workflows
| 工具名 | 用途 | 必填参数 | dangerous | V3 端点 |
|---|---|---|---|---|
| `run_cleaning_task` | 组合封装：capabilities→task_resources→create_task_definition→start_task→轮询 | robot_sn, task_name, map_id, resource_ids: list[str], mode="sweep", strength?, loop_count=1, wait_seconds=30 | ✔ | 组合（见左侧） |
| `wait_for_command` | 轮询 commands/status/get 至终态 | robot_sn, request_id, timeout_seconds=60 | | 轮询 `robots/commands/status/get` |

## reference / memory（本地，不调上游）
| 工具名 | 用途 | 必填参数 | dangerous | V3 端点 |
|---|---|---|---|---|
| `lookup_error_code` | 按错误码检索 `error-codes.md` 与 `experience.md` 的匹配段落；不认识的码先查它，不要猜 | code: str（3–10 位数字） | | 本地参考表（无端点） |
| `remember` | 把一条经证实的可复用经验写入本地 `$SAODI_DATA_DIR/memory.md`（去重、拒绝密钥形态） | lesson: str, scope? | ✔ | 本地文件（无端点） |

### 命令类型对照（commandType，源 command-type-reference.md）
START_FUSION_TASK / SKIP_TASK / PAUSE_TASK / RESUME_TASK / STOP_TASK / CROSS_NAVIGATE / PAUSE_NAVIGATE / RESUME_NAVIGATE / STOP_NAVIGATE。
