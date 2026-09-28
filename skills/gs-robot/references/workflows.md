# 端到端工作流示例

3 个示例对话脚本，展示工具调用顺序与示例参数。所有 SN / ID / 凭据均为占位符，请用实际值替换。dangerous ✔ 工具调用前必须向用户复述并确认。

---

## 示例 1：查看全部机器人状态并汇总

**用户意图**：把账号下所有机器人的当前状态汇总成一张表。

**对话脚本**：
1. 助手：先列出机器人。
   - 工具：`list_robots`（page=1, page_size=20）
   - 返回：`{"list": [{"robotSn": "<SN-A>"}, {"robotSn": "<SN-B>"}, ...], "total": 2}`
2. 助手：批量拉状态快照（≤100 个 SN 一次）。
   - 工具：`get_robot_status`（robot_sn_list: ["<SN-A>", "<SN-B>"]）
   - 返回：`data.list[]` 含 `robotSn / onlineStatus / workState / batteryPercent / currentMapName / taskName`
3. 助手：（可选）对非空闲状态查含义。
   - 工具：`describe_work_state`（work_state: 230）→ `AUTO_TASKING`
4. 助手输出表格：

   | robot_sn | online | workState(名) | 电量 | 当前地图 | 当前任务 |
   |---|---|---|---|---|---|
   | <SN-A> | ONLINE | 230 AUTO_TASKING | 78% | 一楼大厅 | 每日清扫 |
   | <SN-B> | ONLINE | 100 IDLE | 95% | 大堂地图 | — |
   | <SN-C> | OFFLINE | — | — | — | — |

   说明：状态快照最大延迟约 30s，`observedMsTimestamp` 为观测时刻。

---

## 示例 2：给指定机器人在指定地图区域下发一次清扫任务

**用户意图**：让机器人 `<SN>` 在地图 `<map_id>` 的区域 `<region_resource_id>` 执行一次扫尘（sweep）。

**对话脚本**：
1. 助手：先确认机器人在线且空闲。
   - 工具：`get_robot_status`（robot_sn_list: ["<SN>"]）
   - 判定：`onlineStatus=ONLINE` 且 `workState=100`（IDLE）才继续；否则告知用户当前不可下发。
2. 助手：查能力与工作模式（确认 sweep 可用）。
   - 工具：`get_robot_capabilities`（robot_sn: "<SN>"）
3. 助手：查任务资源（拿 workModes + regions 的 mapResourceId）。
   - 工具：`list_task_resources`（robot_sn: "<SN>", map_id_list: ["<map_id>"], include_paths=True, include_regions=True, include_positions=False）
   - 从返回的 `data.workModes[]` 取 `mode="sweep"` 的配置（记下 id/strengthOptions）。
   - 从 `data.maps[].regions[]` 取目标区域的 `mapResourceId` 与 `mapResourceAreaId`，确认 `supportedActions` 含 `sweep`。
4. 助手：（dangerous ✔）向用户复述并确认：
   > 将对机器人 `<SN>` 创建任务定义「SK_<时间戳>」，工作模式 sweep（middle），资源：区域 `<region_name>`（map_id=<map_id>），loop_count=1。确认？
5. 用户确认后：
   - 工具：`create_task_definition`（
     robot_sn="<SN>",
     task_name="SK_20260928_1030",
     work_mode={"mode": "sweep", "strength": "middle"},
     map_resource_list=[{"map_id": "<map_id>", "map_resource_id": "<region_resource_id>", "map_resource_type": "region"}],
     loop_count=1）
   - 注意：`create_task_definition` 成功返回 `data` 为空对象，内部 `fusion_task_id` 不直接回显。
6. 助手：拿 fusion_task_id。
   - 工具：`list_task_definitions`（robot_sn: "<SN>", page=1, pagesize=5）
   - 按 `task_name` 匹配最新一条，取 `fusionTaskId`。
7. 助手：（dangerous ✔）向用户复述并确认启动：
   > 将启动任务定义 `<fusion_task_id>`，loop_count=1。确认？
8. 用户确认后：
   - 工具：`start_task`（robot_sn: "<SN>", fusion_task_id: "<fusion_task_id>", loop_count:1）
   - 返回：`data.requestId`、`data.cmdStatus=6`、`data.taskInstanceId`。
9. 助手：轮询命令状态确认下发与执行。
   - 工具：`get_command_status`（robot_sn: "<SN>", request_id: "<requestId>"）
   - 或 `wait_for_command`（robot_sn: "<SN>", request_id: "<requestId>", timeout_seconds=60）
   - 说明：`cmdStatus=6` 仅代表下发成功，需继续跟踪 `workState` 变为 230（AUTO_TASKING）才算真正开始执行。
10. 助手输出：已下发，requestId=`<...>`，taskInstanceId=`<...>`，机器人已进入 AUTO_TASKING。

**简化路径**（信任封装）：可直接用 `run_cleaning_task`（robot_sn, task_name, map_id, resource_ids=["<region_resource_id>"], mode="sweep", strength="middle", loop_count=1, wait_seconds=30），内部自动跑步骤 2-9；但因 dangerous ✔，调用前仍需复述确认。

---

## 示例 3：创建每周定时计划

**用户意图**：给机器人 `<SN>` 创建一个每周一至周五 02:15 执行的扫尘计划（定量任务，全区）。

**对话脚本**：
1. 助手：查任务资源拿 workModes 与 map 资源。
   - 工具：`list_task_resources`（robot_sn: "<SN>", map_id_list: ["<map_id>"], include_paths=True, include_regions=True）
   - 取 `workModes[]` 中 `mode="sweep"`；取 `maps[].regions[]` 一个目标区域的 `mapResourceId`、`mapResourceType="region"`。
2. 助手：（dangerous ✔）向用户复述并确认：
   > 将创建简易排班「每周一至周五 02:15 清扫」，模式 sweep，全区（site_mode=0），开始日期 2026-09-28，长期有效至 2099-12-31。确认？
3. 用户确认后：
   - 工具：`create_simple_schedule`（
     robot_sn: "<SN>",
     task_name: "每周工作日清扫_02:15",
     work_mode: {"mode": "sweep"},
     map_resource_list: [{"map_id": "<map_id>", "map_resource_id": "<region_resource_id>", "map_resource_type": "region"}],
     plan_execute_type: 2,  // 2=定量 QUANTITATIVE_SCH_TASK
     plan_repeat_type: 2,   // 2=每周
     plan_repeat_weekly: [1, 2, 3, 4, 5],  // 0=周日 … 6=周六；1-5=周一至周五
     plan_start_date: "2026-09-28",
     plan_start_time: "02:15",
     plan_stop_date: "2099-12-31",
     site_mode: 0)
   - 返回：`data.planUuid`、`planCommitNo`、`semesterUuid`。
4. 助手：（可选）按日查预排任务确认已入库。
   - 工具：`list_schedule_pre_tasks`（robot_sn: "<SN>", date: "2026-09-28"）
   - 在 `data.preTasks[]` 中按 `planUuid` 核对。
5. 助手输出：计划已创建，planUuid=`<...>`，将从 2026-09-28 起每周一至周五 02:15 执行。

**注意事项**：
- `plan_repeat_type=2`（每周）时 `plan_repeat_weekly` 必填且非空；`plan_repeat_type=0`（单次）时省略。
- `plan_execute_type=1`（定时 TIMED_SCHEDULING_TASK）需填 `plan_stop_time`（HH:mm 24h，不可跨午夜）；`plan_execute_type=2`（定量）可省略 `plan_stop_time`。
- `site_mode=0` 全区时禁止传 `site_id`；`site_mode=1` 时 `site_id` 必填。
- 开始日期不能早于当天；当天则开始时间须晚于当前时间。
- 改/删用 `update_simple_schedule` / `delete_simple_schedule`（均 dangerous ✔，需 plan_uuid）。
