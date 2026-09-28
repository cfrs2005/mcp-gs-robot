"""Multi-step task workflows built on the same registered V3 tools."""

from __future__ import annotations

import asyncio
from time import monotonic

from pydantic import Field

from .registry import ToolInputError, invoke, tool
from .v3_tools import CommandId, Robot


class WaitCommand(CommandId):
    timeout_seconds: int = Field(default=60, ge=0)


async def _poll(v3, robot_sn: str, request_id: str, timeout_seconds: int):
    deadline = monotonic() + timeout_seconds
    while True:
        status = await invoke("get_command_status", {"robot_sn": robot_sn,
                                                       "request_id": request_id}, v3)
        code = status.get("cmdResultCode")
        cmd_status = status.get("cmdStatus")
        # 6 means delivery succeeded, NOT that cleaning finished. Other non-pending
        # statuses with a result code are treated as terminal delivery failures.
        if cmd_status == 6 or (cmd_status not in (0, 1, 2) and code not in (None, "")):
            return status
        remaining = deadline - monotonic()
        if remaining <= 0:
            return {**status, "timed_out": True}
        await asyncio.sleep(min(3, remaining))


@tool(name="wait_for_command", description="等待命令投递终态 / Wait for command delivery", category="workflows")
async def wait_for_command(v3, args: WaitCommand):
    return await _poll(v3, args.robot_sn, args.request_id, args.timeout_seconds)


class CleaningTask(Robot):
    task_name: str
    map_id: str
    resource_ids: list[str] = Field(min_length=1)
    mode: str = "sweep"
    strength: str | None = None
    loop_count: int = 1
    wait_seconds: int = Field(default=30, ge=0)


@tool(name="run_cleaning_task", description="创建并启动清洁任务 / Create and start cleaning task", dangerous=True, category="workflows")
async def run_cleaning_task(v3, args: CleaningTask):
    capabilities = await invoke("get_robot_capabilities", {"robot_sn": args.robot_sn}, v3)
    resources = await invoke("list_task_resources", {"robot_sn": args.robot_sn,
                                                      "map_id_list": [args.map_id]}, v3)
    selected = {}
    for map_data in resources["maps"]:
        if map_data["mapId"] != args.map_id:
            continue
        for group in ("paths", "regions", "positions"):
            for resource in map_data.get(group, []):
                if resource["mapResourceId"] in args.resource_ids:
                    selected[resource["mapResourceId"]] = {
                        "mapId": map_data["mapId"],
                        **{key: resource[key] for key in (
                            "mapResourceId", "mapResourceType", "mapResourceName",
                            "mapResourceAreaId") if resource.get(key) is not None},
                    }
    missing = set(args.resource_ids) - selected.keys()
    if missing:
        raise ToolInputError(f"Unknown resources on map {args.map_id}: {', '.join(sorted(missing))}")
    work_mode = {"mode": args.mode}
    if args.strength is not None:
        work_mode["strength"] = args.strength
    created = await invoke("create_task_definition", {
        "robot_sn": args.robot_sn, "task_name": args.task_name,
        "work_mode": work_mode, "map_resource_list": [selected[key] for key in args.resource_ids],
        "loop_count": args.loop_count,
    }, v3)
    fusion_task_id = created.get("fusionTaskId") if isinstance(created, dict) else None
    definitions = None
    if not fusion_task_id:
        definitions = await invoke("list_task_definitions", {
            "robot_sn": args.robot_sn, "task_name": args.task_name,
        }, v3)
        matches = [item for item in definitions["list"] if item.get("taskName") == args.task_name]
        if len(matches) != 1 or not matches[0].get("fusionTaskId"):
            raise ToolInputError("Cannot uniquely identify created task by task_name; task was created but not started")
        fusion_task_id = matches[0]["fusionTaskId"]
    started = await invoke("start_task", {"robot_sn": args.robot_sn,
                                          "fusion_task_id": fusion_task_id,
                                          "loop_count": args.loop_count}, v3)
    status = await _poll(v3, args.robot_sn, started["requestId"], args.wait_seconds)
    return {"capabilities": capabilities, "task_resources": resources,
            "create_task_definition": created, "list_task_definitions": definitions,
            "start_task": started, "get_command_status": status,
            "final_status": "timeout" if status.get("timed_out") else status.get("cmdStatus")}
