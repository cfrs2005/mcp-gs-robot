# Call experience (Memory)

General experience gathered while testing the interfaces for real. The Saodi agent loads this file in every new session. It does not repeat rules already in `SKILL.md` or `domain.md`; it only records what the documentation does not say and you learn by hitting it.

**Writing rules**: record only general behaviour and how to handle it. Never write any robot SN, traceId, requestId, account, secret, token, customer name, site name or address. Experience that should not be open-sourced goes into the private directory `SAODI_CONTEXT_DIR`, or into the local memory file `$SAODI_DATA_DIR/memory.md` (`saodi memory add`, or the agent's `remember` tool).

## Error codes

- **110003 `Robot is not bound to the current user.`**: the current open-platform credentials (application) are not bound to this robot, or lack permission for this kind of data. Most common on report endpoints (`list_task_reports`, `get_task_report_map_images`), while status and map endpoints for the same robot may work fine. It is an account-side configuration problem; changing parameters or retrying does not help. Tell the user plainly and ask them to check the robot binding and API permissions on the open platform. Field-tested: the binding check of the report endpoints and that of status / maps / task commands are **two separate relationships** — a robot whose status you can read and to which you can send tasks may still be judged "not bound" by the report endpoints (the same response as for a non-existent SN). **110003 ≠ no reports**: reports visible in the cloud web console / user account may be invisible to the open-platform application; do not answer "this robot has no task reports", say "the current open-platform credentials are not bound to this robot, so its reports are not visible". Self-check: if the SN is not in the `list_robots` result, the application is not bound to it and the robot must be bound to the application on the open platform.
- **`taskreports/page` without `robotSn` returns the whole tenant's reports** (the documentation marks it required; the upstream does not actually enforce it). The tool layer must keep `robot_sn` required; do not drop it to get around 110003.
- **230003 `Robot ... routing failed.`**: the platform cannot route to the robot, which basically means the robot is offline (or has not connected to the cloud for a long time). An offline robot returns this from almost every real-time V3 endpoint. Check `onlineStatus` with `get_robot_status` first; if it is offline, stop and say so instead of trying endpoint after endpoint.
- **One 230003 fails the whole batch status call**: if a single SN in the `robots/status/get` list cannot be routed, the entire request returns 230003. Most offline robots do return an `onlineStatus=OFFLINE` snapshot; only a few "long disconnected" ones return 230003. Before a batch status query, filter by the `online` field of `list_robots` and query only the online ones.
- **100026 rate limit: no more than about 20 calls per second.** Throttle per-robot re-queries and concurrent batches (this repository's REST fallback uses a serial 0.1 s interval); do not saturate it with concurrency.
- **HTTP 422 from the HTTP server is not always a caller parameter error**: if the parameters match the schema and it still returns 422, the upstream response may disagree with the local model (a map list once lacked a field). Tell the user the symptom and the tool name, and do not keep retrying with modified parameters.

## Maps and IDs

- In some environments `list_robot_maps` items only have `displayName`, `mapVersionId` and `robotMapUuid`, without `mapId`. In that case `robotMapUuid` is the map id used by other endpoints (this repository back-fills it into `map_id`).
- Other sources of a map id: `list_task_definitions[].mapResourceList[].mapId`, and the map IDs returned by `list_map_resources` / `list_task_resources`. When the sources disagree, the latest `list_task_resources` result wins.
- For read-only exploration, prefer an online robot; an offline one only yields 230003 and tells you nothing.

## Commands and polling

- After `start_task` / `navigate_home` returns `cmdStatus=6`, `wait_for_command` ends immediately — it waits for the "delivery terminal state". To confirm the robot really started, check `get_robot_status` again for workState entering 230 (task) or 170 (navigation), and remind the user that snapshots lag about 30 seconds, so seeing the old state right after sending is normal.
- When the command history (`list_command_history`) is empty, `get_command_status` / `wait_for_command` have no usable `request_id`; do not make one up.

## Empty data is not a fault

- An empty `list_schedules`, a command history with `totalSize=0` or no task reports usually just means the robot has no schedules / has never received a command / has never run a task. Say "there are none"; do not infer an interface fault or a permission problem (permission problems come with an explicit error code, such as 110003).
