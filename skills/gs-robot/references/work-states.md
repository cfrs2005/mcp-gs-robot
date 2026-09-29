# workState 工作状态码表

来源：https://developer.gs-robot.com/v3docs/en_US/Robot%20Work%20State%20Reference（`POST /openapi/v3/robots/status/get` 返回）。`workState` 为机器人原始工作状态码，透传不转换。「运维含义/建议动作」列为本 Skill 编写建议。

| workState | 状态码 | 描述 | 运维含义/建议动作 |
|---|---|---|---|
| 0 | WORK_STATE_UNSPECIFIED | Unspecified | 状态未指定，通常不应出现；若持续返回，建议重新拉取状态或检查机器人上报 |
| 100 | IDLE | Idle | 空闲，可下发任务；如需作业直接 start_task |
| 110 | UNINT | Uninitialized | 未初始化，等待机器人启动完成；暂不下发任务 |
| 140 | RECODING_PATH | Recording path | 正在录制路径，勿打断；等待结束后再操作 |
| 150 | RECODING_AREA | Recording area | 正在录制区域，勿打断 |
| 160 | SAVING_MAP | Saving map | 正在保存地图，勿打断；结束后再切换地图或下发任务 |
| 170 | NAVIGATING | Navigating | 正在导航中；如要改任务，先 stop_navigation 或等待到达 |
| 180 | MANUAL_CHARGING | Manual charging | 人工充电中；不建议下发任务，等待充电结束 |
| 190 | AUTO_CHARGING | Auto charging | 自动回充中；电量充足后会转 IDLE，可在电量足够后下发任务 |
| 200 | WORKSTATION_ADD_OR_EXHAUST_WATER | Workstation add/exhaust water | 工作站上/排水进行中；等待完成后下发任务 |
| 210 | MANUAL_TASK | Manual task | 人工任务执行中；远程任务可能冲突，先确认 |
| 220 | AUTO_TASK_PAUSED | Auto task paused | 自动任务已暂停；可 resume_task 恢复或 stop_task 终止 |
| 230 | AUTO_TASKING | Auto task in progress | 自动任务执行中；如要改派，先 stop_task |
| 240 | NAVIGATING_PAUSED | Navigation paused | 导航已暂停；可 resume_navigation 或 stop_navigation |
| 250 | SCANNING_MAP | Scanning map | 扫图中，勿打断 |
| 260 | ELEVATOR_PAUSE | Elevator paused | 电梯暂停状态；等待电梯流程结束 |
| 270 | REMOTE_WAKE_UP | Remote wake up | 远程唤醒中；等待唤醒完成 |
| 300 | WAITING_FOR_WORK_STATION | Waiting for workstation | 等待工作站；检查工作站是否在线/可用 |
| 310 | RESERVING_WORKSTATION | Reserving workstation | 预约工作站中；等待预约结果 |
| 320 | WAITING_FOR_ELEVATOR | Waiting for elevator | 等待电梯；检查电梯对接配置 |
| 330 | IN_ELEVATOR | In elevator | 在电梯内；跨层任务进行中，勿打断 |
| 340 | NAVI_TO_ELEVATOR | Navigating to elevator | 正前往电梯；等待到达 |
| 350 | ONCALL_ARRIVED | On-call arrived at summon point | 已到达召唤点；可下发下一任务 |
| 360 | LOW_POWER_COMING_SOON | Countdown to low power mode | 即将进入低电量模式；建议先确认电量，必要时回充 |
| 370 | LOW_POWER_ENTER | Entering low power mode | 进入低电量模式；不宜下发作业任务 |
| 380 | LOW_POWER_HOLDING | In low power mode | 低电量保持中；等待充电恢复 |
| 390 | LOW_POWER_ABORTING | Exiting low power mode | 退出低电量模式中；稍后可正常作业 |
| 400 | MANUAL_TRANSITION | Manual transition | 人工过渡状态；等待机器人自动切换 |
| 410 | ROBOT_SLEEP | Robot sleeping | 机器人休眠中；需先唤醒再操作 |
| 420 | PRIMARY_STOP | Primary stop | 主停止；检查是否触发了急停或一级停止 |
| 430 | GATE_STATUS_GOTO | Going to gate | 前往闸机；等待通过 |
| 431 | GATE_STATUS_WAIT | Waiting at gate | 在闸机处等待；检查闸机对接 |
| 432 | GATE_STATUS_PASSING | Passing through gate | 正在通过闸机；勿打断 |
| 440 | EMERGENCY_PARKING | Emergency parking | 紧急停车触发；需现场排查（急停/碰撞/异常），人工复位后再操作 |

### 使用要点
- 状态快照非实时，最大延迟约 30s（`observedMsTimestamp` 为观测时刻）。
- 离线机器人（`onlineStatus=OFFLINE`）运行时字段可能为空，`workState` 也可能缺失。
- 判定「可下发任务」建议：`workState=100`（IDLE）且 `onlineStatus=ONLINE` 且电量充足。
- `cmdStatus=6` 仅代表命令下发成功，需结合 `workState` 变化或 `get_command_status` 终态确认机器人真正开始执行。
