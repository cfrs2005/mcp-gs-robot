# 错误码参考

## 一、任务启动失败错误码

来源：`docs/openapi-v3/task-startup-failure-error-codes.md`。业务响应 `code != 0` 为六位错误码，`msg` 为描述。下表为任务启动失败相关错误码全集。

| 错误码 | 描述 |
|---|---|
| 2010100001 | There is a small problem with the system |
| 2010100002 | There is a small problem with the system |
| 2010100003 | Parameter type illegal |
| 2010100004 | Service request failed |
| 2010100006 | Invalid tag. |
| 2010100007 | Task area unreachable. |
| 2010100008 | Task area does not support the current job type. |
| 2010100009 | Failed to operate data. |
| 2010100010 | Color camera not installed. |
| 2010100011 | Neural stick inspection device not installed. |
| 2010100012 | The temporary task has high priority and cannot execute the scheduled task. |
| 2010100013 | The site is running. |
| 2010100014 | Invalid embedding data |
| 2010100015 | The uploaded data is too large |
| 2010100016 | Low priority of temporary task, unable to execute temporary task. |
| 2010100017 | Duplicate task name. Please set a new one. |
| 2010100018 | Version conflict, robot data has been updated. |
| 2010100020 | HTTP request error |
| 2010100021 | Parameter is empty |
| 2010100022 | File copy failed |
| 2010100023 | Login failed |
| 2010100024 | User not found |
| 2010100025 | Password is empty |
| 2010100026 | Username is empty |
| 2010100027 | Parse server response error |
| 2010100028 | Function under construction |
| 2010100029 | Alert Invalid |
| 2010100030 | Level invalid |
| 2010100031 | Usage type not supported. |
| 2010100032 | System anomaly, please check. |
| 2010100033 | Failed to obtain floor lamp |
| 2010100034 | Failed to start recording obstacles |
| 2010100035 | Deployment data write failed |
| 2010100036 | Failed to query local LoRA address. |
| 2010100037 | Failed to set local LoRA address |
| 2010100038 | Failed to open camera |
| 2010100039 | This feature is not supported. |
| 2010100040 | Failed to operate the tripod camera. |
| 2010100041 | Action JSON format error |
| 2010100042 | Service call error |
| 2010105001 | Please set cleaning time within 8 hours. |
| 2010105002 | Task time conflict, please create a new schedule. |
| 2010105003 | Start time cannot be set in the past. |
| 2010105004 | Task time cannot be less than 1 minute. |
| 2010105005 | The current task is too close to the start time, it should be greater than 1 minute. |
| 2010105006 | The current task is too close to the end time of the previous task, it should be greater than 1 minute. |
| 2010105007 | Changing a recurring plan to a one-time plan is not allowed. |
| 2011200001 | User limit |
| 2011200002 | User type error |
| 2011200003 | Username is empty |
| 2011200004 | The password is empty. |
| 2011200005 | Duplicate username |
| 2011200006 | System error, encryption failed. |
| 2011200007 | The admin user cannot delete. |
| 2011200008 | The user cannot delete. |
| 2011200009 | User has logged in |
| 2011200010 | User does not exist. |
| 2011200011 | Incorrect password |
| 2011200012 | Not logged in, unable to operate |
| 2011200013 | Non-administrators cannot perform this operation. |
| 2011200014 | No permission to operate |
| 2011200015 | The old password is empty. |
| 2011200016 | Please restart the device before deleting. |
| 2020100001 | Failed to operate data file |
| 2020100002 | Failed to copy file |
| 2020100003 | Map not found by ID. |
| 2020100004 | Map in use |
| 2020100005 | Site is empty or does not exist. |
| 2020100006 | Map file corrupted |
| 2020100007 | Map loading |
| 2020100008 | Map scene invalid |
| 2020100009 | Failed to set map scene |
| 2020100010 | Failed to load map scene |
| 2020100011 | The map does not exist! |
| 2020100012 | Map name already exists |
| 2020100013 | Task unreachable, please choose another task |
| 2020100014 | The region of the current task does not match the map partition. |
| 2020100015 | The task is not on the current localization map. Please switch to the correct map in the localization interface and retry after localization succeeds. |
| 2020100016 | Map scene JSON is empty |
| 2020100017 | Failed to update scene mode |
| 2020100018 | Initial point not found |
| 2020100019 | Current initial point not found. |
| 2020100020 | Unable to obtain current location |
| 2020100021 | The navigation point does not exist! |
| 2020100022 | The location name already exists. |
| 2020100023 | The work point is in an unknown area. |
| 2020100024 | The starting point is in an unknown area |
| 2020100025 | Unable to read current RFID |
| 2020100026 | Location data is empty. |
| 2020100027 | Position unsafe |
| 2020100028 | Initial point name is already in use. |
| 2020100029 | Location group not found |
| 2020100030 | Location group name is already in use. |
| 2020100031 | Path not found |
| 2020100032 | Path name already exists |
| 2020100033 | Navigation point is located in an unknown area. |
| 2020100034 | Maximum number of points reached |
| 2020100035 | Path preview failed. Please adjust the area and try again. |
| 2020100036 | Path save failed, please try again. |
| 2020100037 | Path preview failed. Please adjust the area and try again. |
| 2020100038 | Unable to add a station at this location. Please select another location. |
| 2020100039 | Point distance is too close. |
| 2020100040 | Failed to download map data file. |
| 2020100041 | The task is either not selected or has been deleted. Please select a task on the robot and try again. |
| 2020100042 | Task queue already exists |
| 2020100043 | There is a waiting point ahead of the workstation. |
| 2020100044 | Waiting point is located in front of the workstation. |
| 2020100045 | Path not found |
| 2020100046 | Path group not found |
| 2020100047 | Path group name is already in use. |
| 2020100048 | Path unsafe |
| 2020100049 | Starting point is unsafe |
| 2020100050 | Insufficient waypoints |
| 2020100051 | Path file corrupted |
| 2020100052 | Password length is not 32 bits. |
| 2020100053 | Ciphertext mismatch |
| 2020100054 | Failed to write password |
| 2020100055 | Password verification failed |
| 2020100056 | Failed to initialize encryption library |
| 2020100057 | Path file parsing error |
| 2020100058 | Area path generation error |
| 2020100059 | Path optimization error |
| 2020100060 | Path generation error |
| 2020100061 | partition name already exists |
| 2020100062 | partition name is null |
| 2020100063 | The recorded path is too short and will not be saved. |
| 2020100064 | Recording trajectory data corrupted |
| 2020100065 | Failed to save the path CSV file. |
| 2020100066 | Data service map not found. |
| 2020100067 | Data service file operation error |
| 2020100071 | The map has been associated with a floor. Please go to "Building Management - Floor Management" to remove the association. |
| 2020900001 | Scene does not exist |
| 2020900002 | Failed to retrieve parameters |
| 2021100001 | Audio file not found |
| 2050101001 | Task queue is empty |
| 2050101002 | Task is not in the current map |
| 2050101003 | Task type is not registered |
| 2050101004 | Activation code expired |
| 2050101005 | Add Path Action Error |
| 2050101006 | Scheduled task not found |
| 2050101007 | Scheduled task update failed |
| 2050101008 | Scheduled Task Time Conflict |
| 2050101009 | Task queue parameter error |
| 2050101010 | Data service task queue not found. |
| 2050104001 | Other operations are in progress, please try again later! |
| 2050104002 | Command cancelled by offline user |
| 2050104003 | Command cancelled by offline user |
| 2050104004 | Data service task queue already exists. |
| 2050104005 | Remote control ended. |
| 2050104006 | Unsafe condition detected before movement |
| 2070401001 | Please manually empty the sewage tank before operating |
| 2070401002 | Operation too frequent, please wait |
| 2070401003 | Unsafe condition detected during movement |
| 2070401004 | Failed to upload work status |
| 2070401005 | Failed to upload health status |
| 2070401006 | Failed to upload device status |
| 2070401007 | Upload operation log failed |
| 2070401008 | Failed to upload system logs |
| 2070401009 | Failed to download uploaded map information. |
| 2070401010 | Uploadable map not found. |
| 2070401011 | The map name is already in use on the server. |
| 2070401012 | The initial point name has already been used on the server. |
| 2070401013 | The path name is already in use on the server. |
| 2070401014 | Failed to parse path filename from URL |
| 2070401015 | Failed to parse initial point from server. |
| 2070401016 | Failed to download path CSV file. |
| 2070401017 | Failed to parse map PGM filename from URL |
| 2070401018 | Failed to parse map PNG file name from URL |
| 2070401019 | Failed to parse map YAML file name from URL |
| 2070401020 | Failed to parse map data file name from URL |
| 2070401021 | Failed to save map data file. |
| 2070401022 | Failed to download map YAML file |
| 2070401023 | Failed to save map YAML file. |
| 2070401024 | Failed to download map PNG file. |
| 2070401025 | Failed to save map PNG file. |
| 2070401026 | Failed to download map PGM file. |
| 2070401027 | Failed to save map PGM file |
| 2070401028 | Failed to upload map information. |
| 2070401029 | Failed to upload map YAML file. |
| 2070401030 | Failed to upload map PNG file. |
| 2070401031 | Failed to upload map PGM file. |
| 2070401032 | Failed to upload map data file. |
| 2070401033 | Failed to upload initial point. |
| 2070401034 | Upload path failed |
| 2070401035 | Failed to upload path CSV file |
| 2100101001 | I'm lost. Please help me find my location |
| 2100101002 | This operation cannot be performed while scanning |
| 2100101003 | This operation cannot be performed while saving map |
| 2100101004 | This operation cannot be performed in the recording path |
| 2100101005 | This operation cannot be performed in the recording area path |
| 2100101006 | Currently executing a cross-floor task, unable to perform this operation. |
| 2100101007 | The operation cannot be performed while the task is being executed |
| 2100101008 | The operation cannot be performed while navigating |
| 2100101009 | This operation cannot be performed in the elevator |
| 2100101010 | This operation cannot be performed during OTA upgrade |
| 2100101011 | In summoning mode. |
| 2100101012 | Call function not enabled |
| 2100101013 | Data updating, unable to execute this operation. |
| 2100101014 | Powerful washing in progress |
| 2100101015 | Scanning program has stopped. |
| 2100101016 | The scanning program is running. |
| 2100101017 | The task cannot be executed in boot mode. Please end boot mode and try again |
| 2100101018 | Map loading timed out, please try again. |
| 2100101019 | Path program is already running. |
| 2100101020 | CATEGORY ONE STOP TRIGGERED |
| 2100101021 | Path program has stopped. |
| 2100101022 | Path program status error |
| 2100101023 | Path recording program is already running. |
| 2100101024 | Path recording program has stopped. |
| 2100101025 | Recording path program status error |
| 2100101026 | Calibration program for Kinect is already running. |
| 2100101027 | Calibration Kinect program has stopped. |
| 2100101028 | Calibration of Kinect ground plane failed. Please adjust the robot's position. |
| 2100101029 | Calibration of Kinect wall failed. Please adjust the robot's position. |
| 2100101030 | Cruise program is already running. |
| 2100101031 | Cruise program has stopped. |
| 2100101032 | Failed to start scanning map, please try again later. |
| 2100101033 | Stop scanning map error, the map will not be saved. |
| 2100101034 | Cancel scanning map error, the map will not be saved. |
| 2100101035 | Map scanning is not running. |
| 2100101036 | Scan map data is empty. |
| 2100101037 | Failed to start path recording |
| 2100102001 | The emergency stop button is photographed, and this operation cannot be performed |
| 2100102002 | This operation cannot be performed during manual charging |
| 2100102003 | This operation cannot be performed during automatic charging |
| 2100102004 | This operation cannot be performed in a manual job |
| 2100102005 | User cancelled restart |
| 2100102006 | Initialization cancelled |
| 2100102007 | Failed to retrieve the location, please try again |
| 2100102008 | There are alarms that affect task execution |
| 2100102009 | Robot reboot failed |
| 2100102010 | Robot Rebooting |
| 2100102011 | The robot is being maintained at the workstation |
| 2100102012 | The robot is initializing |
| 2100102013 | System busy, please contact the administrator or try again later. |
| 2100102014 | Fully charged manually, not confirmed by clicking on the machine screen |
| 2100102015 | Need to confirm whether the current map is correct |
| 2100102016 | The robot is in manual mode |
| 2100102017 | The operation is not supported, please confirm the robot version |
| 2100102018 | There are no tasks under execution currently |
| 2100102019 | There is no navigation performed currently |
| 2100102020 | This operation cannot be performed in remote wake-up mode |
| 2100102021 | Hillside assistance in progress, please try again later. |
| 2100102022 | The foot pedal is depressed and the operation fails |
| 2100102023 | The robot has not completed the initialization of steering change |
| 2100102024 | Unable to perform this operation in maintenance mode. |
| 2100102025 | The machine is currently resting. |
| 2100102026 | Hub self-check not completed. |
| 2100102027 | Transition in progress |
| 2100102028 | The hood is not closed |
| 2100102029 | The robot is on the workstation, please retry after retreating from the workstation |
| 2100102030 | Emergency Parking Activated |
| 2100102031 | This operation cannot be performed in slope assist mode. |
| 2100102033 | Failed to exit low battery mode. |
| 2100102037 | The robot is passing through the gate, please wait |
| 2100102038 | Please place the robot on the workstation or charging dock and ensure it is charging. |
| 2100102039 | Robot self-cleaning in progress. Please wait. |
| 2100102040 | This robot does not support workstation. |
| 2100102041 | The robot is already paired with a charging dock or workstation. If you need to replace it, please unpair first. |
| 2100102042 | Workstation firmware OTA in progress, please retry later. |
| 2100102043 | Current cleaning mode does not support reset. |
| 2100102044 | Other operations are in progress. Please exit the current page and re-enter before starting |
| 2100102050 | Due to weather conditions, the robot will not perform this cleaning task. |
| 2100102051 | Please Move Away from Charging Station Before Using This Function |
| 2100103001 | No workstation or charging point found |
| 2100103002 | I am lost |
| 2100103003 | I am lost |
| 2100103004 | I am lost |
| 2100103005 | The site is loading. |
| 2100103006 | The map is unavailable. |
| 2100103007 | I am lost |
| 2100103008 | Task cannot be executed: hand pulled up |
| 2100103009 | This site property is not allowed to be saved. |
| 2100103010 | Elevator point does not exist, unable to perform cross-floor task. |
| 2100103011 | Positioning not ready |
| 2100103012 | Different LiDAR detected, please contact customer service. |
| 2100103013 | Map data error, please restart the machine. |
| 2100103014 | MOVEBASE not ready |
| 2100103015 | MOVEBASE Key invalid |
| 2100103016 | Mapping USB Key not properly inserted, please check the machine. |
| 2100104008 | The machine has no auxiliary water tank. |
| 2100200000 | There are alarms that affect task execution |
| 2100200001 | Need to resupply |
| 2100200002 | Failed to confirm floor (map) |
| 2100401001 | QR Code Function Conflict, Please Ensure No Other QR Code Service Is in Use |
| 2100401002 | QR Code Retry Failed, Please Exit and Retry |
| 2100401003 | QR Code Service Shutdown Failed, Please Confirm Shutdown Parameters Are Correct |
| 2100401004 | QR Code Function Not Enabled |
| 2100401005 | QR Code Service Startup Failed |
| 2100402001 | Task execution failed, please check the device status |
| 2100402002 | Obstacle detected, unable to perform task. Please move the vehicle to an open area and restart the task. |
| 2100402003 | The area freezing start time must be at least one minute longer than the current time |
| 2100402004 | The robot is already at the charging pile |
| 2100402005 | Not in maintenance mode |
| 2100402006 | Maintenance item(s) running. |
| 2100402007 | No maintenance item(s) running. |
| 2100402008 | The maintenance item does not exist. |
| 2100402009 | The request does not match the current maintenance item. |
| 2100402010 | The current maintenance item is not completed. |
| 2100501001 | Remote deployment does not exist. |
| 2100501002 | Remote deployment state switching failure |
| 2100501003 | QR code positioning not ready, please initialize first. |
| 2100501004 | Remote deployment failed. Please check your network and try again. |
| 2100501005 | Communication between the device and the cloud is abnormal. The system is retrying. Please wait patiently. |
| 2100501006 | QR code message not received. |
| 2100501007 | QR code already exists. Please delete it first. |
| 2101201001 | Workstation other exception, please contact administrator |
| 2101201003 | The communication between the robot and the Workstation has timed out. Please check if the Workstation is powered off. |
| 2101201004 | Workstation reservation failed, please check if Workstation is occupied |
| 2101201005 | Robot Emergency Stop Button pressed |
| 2101201006 | Robot charging status abnormal, attempting to re-dock |
| 2101201007 | Mobile Water Tank not connected, please connect water and electrical connectors to Mobile Water Tank |
| 2101201008 | User actively ended maintenance |
| 2101201010 | Mobile Water Tank clean water pump wire broken, please check connection between Workstation and Mobile Water Tank |
| 2101201022 | Water filling timeout, please confirm if faucet is properly opened |
| 2101201023 | Workstation not configured with clean water filling function |
| 2101201024 | Workstation clean water ball valve overcurrent, please restart Workstation and try again |
| 2101201025 | Mobile Water Tank clean water pump short circuit, please check clean water pump and wiring |
| 2101201026 | Robot Dirty Water Tank liquid level rising during clean water filling, please check if Clean Water Tank is leaking |
| 2101201027 | Mobile Water Tank Clean Water Tank empty, please add clean water |
| 2101201043 | Drainage timeout, please check if robot drainage pipeline is blocked |
| 2101201044 | Workstation not configured with sewage drainage function |
| 2101201045 | Robot drainage pump operating normally but unable to drain, please check if sewage filter cotton is blocked |
| 2101201046 | Workstation drainage pipeline blocked, please clean Workstation buffer tank drainage pipeline |
| 2101201047 | Mobile Water Tank Dirty Water Tank full, please empty sewage |
| 2101201048 | Robot Dirty Water Tank not in place |
| 2101201060 | No need to perform Squeegee Self-cleaning this time |
| 2101201062 | Robot Dirty Water Tank not emptied, Squeegee Self-cleaning cannot be performed |
| 2101201063 | Workstation Self-cleaning sink not in place |
| 2101201064 | Workstation Self-cleaning sink liquid level sensor triggered, please clean liquid level sensor |
| 2101201065 | Dirty Water Tank not emptied after Squeegee Self-cleaning, please clean Dirty Water Tank Filter Basket and sewage filter cotton |
| 2101201066 | Drainage valve not closed, Squeegee Self-cleaning cannot be performed |
| 2101201067 | HEPA not installed, Squeegee Self-cleaning cannot be performed |
| 2101201068 | Robot head cover not closed, Squeegee Self-cleaning cannot be performed |
| 2101201069 | Squeegee Self-cleaning not completed, full machine Dirty Water Tank Self-cleaning cannot be performed |
| 2101201070 | This robot hardware version does not support Workstation |
| 2101201071 | Workstation buffer tank not in place |
| 2101201072 | Workstation self-cleaning sink water filling timeout. Please check if water supply is stopped or water flow is too low. |
| 2101201091 | User actively ended robot Dirty Water Tank Self-cleaning |
| 2101201092 | Robot Dirty Water Tank Self-cleaning paused too long, automatically ended |
| 2101201093 | Workstation drainage pipeline blocked, please clean Workstation buffer tank drainage pipeline |
| 2101201094 | Robot Clean Water Tank liquid level too low, cannot perform Dirty Water Tank Self-cleaning |
| 2101201095 | Robot Dirty Water Tank not emptied, cannot perform Dirty Water Tank Self-cleaning |
| 2101201096 | Workstation buffer tank liquid level float stuck, please clean dirt on liquid level float surface |
| 2101201097 | Robot Dirty Water Tank liquid level float stuck, please clean dirt on liquid level float surface |
| 2110100001 | Please redraw the failed elevator area update. |
| 2111000001 | Restoration failed, only extended maps can be restored. |
| 2111000002 | Restoration failed, map file is already up to date. |
| 2111000003 | Restoration failed, failed to delete map file. |
| 2111000004 | Restoration failed, failed to decompress map file. |
| 2111000005 | Restoration failed, failed to update map list. |

### 高频错误码快速处置
| 错误码 | 描述 | 建议动作 |
|---|---|---|
| 2010100007 | Task area unreachable | 核对 map_resource_list 是否来自最新 list_task_resources；确认机器人在线且地图未变更 |
| 2010100017 | Duplicate task name | 换 task_name 或先 delete_task_definition 删旧定义 |
| 2010100018 | Version conflict, robot data has been updated | 重新 list_task_resources 取最新 ID 再建/改任务 |
| 2020100003 | Map not found by ID | 用 list_robot_maps 重新拿 map_id |
| 2050104001 | Other operations are in progress | 等待 30-60s 重试；或 get_robot_status 看是否在 AUTO_TASKING |
| 2100101001 | I'm lost | 机器人丢失定位，提示用户现场确认位置/重新建图 |
| 2100102008 | Alarms affect task execution | 提示用户在机器人端查看告警并清除 |
| 2100102030 | Emergency Parking Activated | 现场排查急停/碰撞/异常，人工复位 |

## 二、常见 HTTP / OAuth 错误

| HTTP 状态 | 含义 | 建议动作 |
|---|---|---|
| 401 | 鉴权失败 / token 过期 | 由 token_manager 自动 refresh；若 refresh 失败，提示检查 `GS_CLIENT_ID/SECRET/OPEN_ACCESS_KEY` |
| 400 / 422 | 参数错误 | 检查必填字段、snake_case 拼写、枚举值（region/path/position）、时间格式（yyyy-MM-dd / HH:mm 24h） |
| 403 | 无权限 | 确认机器人是否绑定到当前开发者账号；确认 AccessKey 归属 |
| 404 | 端点不存在 | 核对 `GS_BASE_URL` 是否为 `https://openapi.gs-robot.com/`；确认路径前缀 `/openapi/v3/` |
| 429 | 限流 | 降低调用频率，指数退避重试 |
| 5xx | 上游服务异常 | 重试；持续失败联系平台运维 |
| 502 (HTTP Server) | GausiumAPIError 转换 | 响应体 `error.code` 为六位业务码，查上表 |

### OAuth 相关
| 现象 | 可能原因 | 处置 |
|---|---|---|
| token 接口返回 401 | client_id/client_secret/open_access_key 不匹配 | 核对 quick-start.md 步骤 2-3；`open_access_key` 用的是 AccessKeySecret（通信密钥），不是 AccessKeyID |
| token 24h 内过期 | 默认有效期 24h，`expires_in` 标识 | token_manager 在过期前自动用 refresh_token 刷新 |
| refresh_token 失效 | 超过刷新窗口或被吊销 | 重新走 OAuth 取 token 流程 |
