"""H5-friendly robot REST endpoints backed exclusively by the tool registry."""

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Body, HTTPException, Query

from gs_openapi.core.errors import GausiumAPIError
from gs_openapi.tools import registry
from gs_openapi.v3.api import GausiumV3

from .. import deps

router = APIRouter(prefix="/robots")


async def call(name: str, v3: GausiumV3, **args: Any) -> Any:
    return await registry.invoke(name, args, v3)


@router.get("")
async def list_robots(
    v3: deps.V3Dep, page: int = 1, page_size: int = 20,
) -> Any:
    result = await call("list_robots", v3, page=page, page_size=page_size)
    if isinstance(result, dict):
        result = result.get("list", result.get("robots", result))
    if isinstance(result, list):
        # Legacy v1alpha1/robots names the SN serialNumber; the H5 keys robots by robotSn.
        for item in result:
            if isinstance(item, dict) and "robotSn" not in item and "serialNumber" in item:
                item["robotSn"] = item["serialNumber"]
    return result


# Upstream 230003 "Robot ... routing failed.": the platform cannot route to the robot,
# i.e. it is offline. The batch snapshot endpoint fails as a whole if any SN is offline.
ROBOT_UNREACHABLE = 230003
UNREACHABLE_MESSAGE = "机器人离线或未连接云端"
# Upstream rate limit is < 20 requests/second per app; pace the per-robot fallback well below it.
FALLBACK_INTERVAL_SECONDS = 0.1


def unreachable(sn: str, exc: GausiumAPIError) -> dict[str, Any]:
    """Status placeholder for an unroutable robot; same shape as a snapshot plus error."""
    return {
        "robotSn": sn, "onlineStatus": "OFFLINE", "reachable": False,
        "error": {"code": exc.code, "message": UNREACHABLE_MESSAGE, "trace_id": exc.trace_id},
    }


async def status_list(sns: list[str], v3: GausiumV3) -> list[dict[str, Any]]:
    """Batch status; on 230003 re-query one by one so only offline robots are degraded."""
    try:
        return (await call("get_robot_status", v3, robot_sn_list=sns))["list"]
    except GausiumAPIError as exc:
        if exc.code != ROBOT_UNREACHABLE:
            raise
        if len(sns) == 1:
            return [unreachable(sns[0], exc)]

    async def one(index: int, sn: str) -> list[dict[str, Any]]:
        await asyncio.sleep(index * FALLBACK_INTERVAL_SECONDS)
        return await status_list([sn], v3)

    results = await asyncio.gather(*(one(i, sn) for i, sn in enumerate(sns)))
    return [item for items in results for item in items]


@router.post("/status")
async def batch_status(body: dict[str, Any], v3: deps.V3Dep) -> Any:
    # Validate through the registry model (1..100 SNs) before any upstream call.
    args = registry.get_tool("get_robot_status").input_model.model_validate(body)
    return await status_list(args.robot_sn_list, v3)


@router.get("/{sn}/status")
async def robot_status(sn: str, v3: deps.V3Dep) -> Any:
    for item in await status_list([sn], v3):
        if item["robotSn"] == sn:
            return item
    raise HTTPException(status_code=404, detail="Robot status not found")


@router.get("/{sn}/maps")
async def robot_maps(sn: str, v3: deps.V3Dep) -> Any:
    return await call("list_robot_maps", v3, robot_sn=sn)


@router.get("/{sn}/maps/{map_id}/canvas")
async def map_canvas(sn: str, map_id: str, v3: deps.V3Dep) -> Any:
    return await call("get_map_canvas", v3, robot_sn=sn, map_id=map_id)


@router.get("/{sn}/maps/{map_id}/resources")
async def map_resources(sn: str, map_id: str, v3: deps.V3Dep) -> Any:
    return await call("list_map_resources", v3, robot_sn=sn, map_id_list=[map_id])


@router.get("/{sn}/capabilities")
async def capabilities(sn: str, v3: deps.V3Dep) -> Any:
    return await call("get_robot_capabilities", v3, robot_sn=sn)


@router.get("/{sn}/work-modes")
async def work_modes(sn: str, v3: deps.V3Dep) -> Any:
    return await call("list_work_modes", v3, robot_sn=sn)


@router.get("/{sn}/task-definitions")
async def task_definitions(
    sn: str, v3: deps.V3Dep, page: int = 1, pagesize: int = 20,
) -> Any:
    return await call("list_task_definitions", v3, robot_sn=sn, page=page, pagesize=pagesize)


@router.post("/{sn}/task-definitions")
async def create_task(sn: str, body: dict[str, Any], v3: deps.V3Dep) -> Any:
    return await registry.invoke("create_task_definition", {**body, "robot_sn": sn}, v3)


@router.get("/{sn}/task-definitions/{fusion_task_id}")
async def get_task(sn: str, fusion_task_id: str, v3: deps.V3Dep) -> Any:
    return await call("get_task_definition", v3, robot_sn=sn, fusion_task_id=fusion_task_id)


@router.put("/{sn}/task-definitions/{fusion_task_id}")
async def update_task(
    sn: str, fusion_task_id: str, body: dict[str, Any], v3: deps.V3Dep,
) -> Any:
    return await registry.invoke(
        "update_task_definition", {**body, "robot_sn": sn, "fusion_task_id": fusion_task_id}, v3,
    )


@router.delete("/{sn}/task-definitions/{fusion_task_id}")
async def delete_task(sn: str, fusion_task_id: str, v3: deps.V3Dep) -> Any:
    return await call("delete_task_definition", v3, robot_sn=sn, fusion_task_id=fusion_task_id)


TASK_ACTIONS = {
    "start": "start_task", "pause": "pause_task", "resume": "resume_task",
    "stop": "stop_task", "skip": "skip_task_item",
}
NAV_ACTIONS = {
    "go-home": "navigate_home", "pause": "pause_navigation",
    "resume": "resume_navigation", "stop": "stop_navigation",
}


@router.post("/{sn}/tasks/{action}")
async def task_action(
    sn: str, action: Literal["start", "pause", "resume", "stop", "skip"],
    v3: deps.V3Dep, body: Annotated[dict[str, Any] | None, Body()] = None,
) -> Any:
    return await registry.invoke(TASK_ACTIONS[action], {**(body or {}), "robot_sn": sn}, v3)


@router.post("/{sn}/navigation/{action}")
async def navigation_action(
    sn: str, action: Literal["go-home", "pause", "resume", "stop"],
    v3: deps.V3Dep, body: Annotated[dict[str, Any] | None, Body()] = None,
) -> Any:
    return await registry.invoke(NAV_ACTIONS[action], {**(body or {}), "robot_sn": sn}, v3)


@router.get("/{sn}/commands")
async def commands(
    sn: str, v3: deps.V3Dep, page: int = 1, pagesize: int = 20,
) -> Any:
    return await call("list_command_history", v3, robot_sn=sn, page=page, pagesize=pagesize)


@router.get("/{sn}/commands/{request_id}")
async def command(sn: str, request_id: str, v3: deps.V3Dep) -> Any:
    return await call("get_command_status", v3, robot_sn=sn, request_id=request_id)


@router.get("/{sn}/reports")
async def reports(
    sn: str, v3: deps.V3Dep, page: int = 1, pagesize: int = 20,
    end_time_min: str | None = None, end_time_max: str | None = None,
) -> Any:
    return await call(
        "list_task_reports", v3, robot_sn=sn, page=page, pagesize=pagesize,
        end_time_min=end_time_min, end_time_max=end_time_max,
    )


@router.get("/{sn}/schedules")
async def schedules(sn: str, v3: deps.V3Dep) -> Any:
    return await call("list_schedules", v3, robot_sn=sn)


@router.post("/{sn}/schedules")
async def create_schedule(
    sn: str, body: dict[str, Any], v3: deps.V3Dep,
) -> Any:
    return await registry.invoke("create_schedule", {**body, "robot_sn": sn}, v3)


@router.post("/{sn}/schedules/simple")
async def create_simple_schedule(
    sn: str, body: dict[str, Any], v3: deps.V3Dep,
) -> Any:
    return await registry.invoke("create_simple_schedule", {**body, "robot_sn": sn}, v3)


@router.get("/{sn}/schedules/{plan_id}")
async def schedule(
    sn: str, plan_id: str, v3: deps.V3Dep, year: Annotated[int, Query()],
    month: Annotated[int, Query()], day_of_month: Annotated[int, Query()],
) -> Any:
    return await call(
        "get_schedule", v3, robot_sn=sn, plan_uuid=plan_id, year=year,
        month=month, day_of_month=day_of_month,
    )


@router.put("/{sn}/schedules/{plan_id}")
async def update_schedule(
    sn: str, plan_id: str, body: dict[str, Any], v3: deps.V3Dep,
) -> Any:
    return await registry.invoke("update_schedule", {**body, "robot_sn": sn, "plan_uuid": plan_id}, v3)


@router.delete("/{sn}/schedules/{plan_id}")
async def delete_schedule(
    sn: str, plan_id: str, v3: deps.V3Dep,
    body: Annotated[dict[str, Any] | None, Body()] = None,
) -> Any:
    return await registry.invoke("delete_schedule", {**(body or {}), "robot_sn": sn, "plan_uuid": plan_id}, v3)
