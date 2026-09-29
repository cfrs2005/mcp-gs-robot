"""Typed registry handlers for the V3 business endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..v3.references import describe_work_state as describe_state
from ..v3.references import is_terminal_work_state
from .registry import tool


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Robot(Input):
    robot_sn: str


class RobotMap(Robot):
    map_id: str


class RobotMaps(Robot):
    map_id_list: list[str]
    include_paths: bool | None = None
    include_regions: bool | None = None
    include_positions: bool | None = None


class TaskResources(RobotMaps):
    include_paths: bool = True
    include_regions: bool = True
    include_positions: bool = False


class ListRobots(Input):
    page: int = 1
    page_size: int = 20
    relation: str | None = None


@tool(name="list_robots", description="列出机器人 / List robots")
async def list_robots(v3, args: ListRobots):
    query = {"page": args.page, "pageSize": args.page_size}
    if args.relation is not None:
        query["relation"] = args.relation
    return await v3._client.call_endpoint("list_robots", query_params=query)


class RobotStatus(Input):
    robot_sn_list: list[str] = Field(min_length=1, max_length=100)


@tool(name="get_robot_status", description="查询机器人状态 / Get robot status")
async def get_robot_status(v3, args: RobotStatus):
    page = await v3.robots.get_status(args.robot_sn_list)
    result = page.model_dump(mode="json", by_alias=True)
    for snapshot in result["list"]:
        state = describe_state(snapshot.get("workState"))
        snapshot["work_state_name"] = state[0] if state else None
        snapshot["work_state_desc"] = state[1] if state else None
    return result


class WorkState(Input):
    work_state: int


@tool(name="describe_work_state", description="解释工作状态 / Describe robot work state", local=True)
async def describe_work_state(v3, args: WorkState):
    state = describe_state(args.work_state)
    return {"work_state": args.work_state, "name": state[0] if state else None,
            "description": state[1] if state else None,
            "is_terminal": is_terminal_work_state(args.work_state)}


@tool(name="get_robot_capabilities", description="查询机器人任务能力 / Get task capabilities")
async def get_robot_capabilities(v3, args: Robot):
    return await v3.tasks.get_capabilities(args.robot_sn)


@tool(name="list_robot_maps", description="列出机器人地图 / List robot maps", category="maps")
async def list_robot_maps(v3, args: Robot):
    return await v3.maps.list_maps(args.robot_sn)


@tool(name="get_map_canvas", description="查询地图画布 / Get map canvas", category="maps")
async def get_map_canvas(v3, args: RobotMap):
    return await v3.maps.get_canvas(args.robot_sn, args.map_id)


@tool(name="list_charging_positions", description="列出充电点 / List charging positions", category="maps")
async def list_charging_positions(v3, args: RobotMap):
    return await v3.maps.list_charging_positions(args.robot_sn, args.map_id)


@tool(name="list_map_resources", description="列出地图资源 / List map resources", category="maps")
async def list_map_resources(v3, args: RobotMaps):
    return await v3.maps.list_resources(**args.model_dump())


@tool(name="list_task_resources", description="查询任务资源 / List task resources", category="maps")
async def list_task_resources(v3, args: TaskResources):
    return await v3.maps.list_schedule_resources(**args.model_dump())


@tool(name="list_work_modes", description="查询工作模式 / List work modes", category="tasks")
async def list_work_modes(v3, args: Robot):
    return await v3.tasks.list_work_modes(args.robot_sn)


class PageDefinitions(Robot):
    page: int = 1
    pagesize: int = 20
    site_id: str | None = None
    task_name: str | None = None


@tool(name="list_task_definitions", description="分页查询任务定义 / List task definitions", category="tasks")
async def list_task_definitions(v3, args: PageDefinitions):
    return await v3.tasks.page_definitions(args.robot_sn, args.page, args.pagesize,
                                           site_id=args.site_id, task_name=args.task_name)


class TaskId(Robot):
    fusion_task_id: str


@tool(name="get_task_definition", description="查询任务定义 / Get task definition", category="tasks")
async def get_task_definition(v3, args: TaskId):
    return await v3.tasks.get_definition(args.robot_sn, args.fusion_task_id)


class CreateTask(Robot):
    task_name: str
    work_mode: dict[str, Any]
    map_resource_list: list[dict[str, Any]]
    loop_count: int | None = None
    site_id: str | None = None
    task_advance_config: dict[str, Any] | None = None


@tool(name="create_task_definition", description="创建任务定义 / Create task definition", dangerous=True, category="tasks")
async def create_task_definition(v3, args: CreateTask):
    return await v3.tasks.create_definition(**args.model_dump())


class UpdateTask(TaskId):
    task_name: str | None = None
    work_mode: dict[str, Any] | None = None
    map_resource_list: list[dict[str, Any]] | None = None
    loop_count: int | None = None
    site_id: str | None = None
    task_advance_config: dict[str, Any] | None = None


@tool(name="update_task_definition", description="更新任务定义 / Update task definition", dangerous=True, category="tasks")
async def update_task_definition(v3, args: UpdateTask):
    return await v3.tasks.update_definition(**args.model_dump(exclude_none=True))


@tool(name="delete_task_definition", description="删除任务定义 / Delete task definition", dangerous=True, category="tasks")
async def delete_task_definition(v3, args: TaskId):
    return await v3.tasks.delete_definition(args.robot_sn, args.fusion_task_id)


class StartTask(TaskId):
    loop_count: int | None = None


@tool(name="start_task", description="启动任务 / Start task", dangerous=True, category="tasks")
async def start_task(v3, args: StartTask):
    return await v3.tasks.start(args.robot_sn, args.fusion_task_id, loop_count=args.loop_count)


@tool(name="pause_task", description="暂停任务 / Pause task", dangerous=True, category="tasks")
async def pause_task(v3, args: Robot):
    return await v3.tasks.pause(args.robot_sn)


@tool(name="resume_task", description="继续任务 / Resume task", dangerous=True, category="tasks")
async def resume_task(v3, args: Robot):
    return await v3.tasks.resume(args.robot_sn)


@tool(name="stop_task", description="停止任务 / Stop task", dangerous=True, category="tasks")
async def stop_task(v3, args: Robot):
    return await v3.tasks.stop(args.robot_sn)


@tool(name="skip_task_item", description="跳过任务项 / Skip task item", dangerous=True, category="tasks")
async def skip_task_item(v3, args: Robot):
    return await v3.tasks.skip(args.robot_sn)


def _camel(key: str) -> str:
    first, *rest = key.split("_")
    return first + "".join(part.capitalize() for part in rest)


def _body(args: Input) -> dict[str, Any]:
    return {_camel(key): value for key, value in args.model_dump(exclude_none=True).items()}


class SimpleSchedule(Robot):
    task_name: str
    site_mode: int
    work_mode: dict[str, Any]
    map_resource_list: list[dict[str, Any]]
    plan_execute_type: int
    plan_repeat_type: int
    plan_start_date: str
    plan_start_time: str
    site_id: str | None = None
    loop_count: int | None = None
    plan_repeat_weekly: list[int] | None = None
    plan_stop_date: str | None = None
    plan_stop_time: str | None = None
    task_advance_config: dict[str, Any] | None = None
    client_time: int | None = None
    client_time_zone: str | None = None


@tool(name="create_simple_schedule", description="创建简易排班 / Create simple schedule", dangerous=True, category="schedules")
async def create_simple_schedule(v3, args: SimpleSchedule):
    return await v3.schedules.simple_create(**_body(args))


class SimpleScheduleChange(Robot):
    plan_uuid: str
    year: int
    month: int
    day_of_month: int
    operation_type: int
    client_time_zone: str | None = None
    client_time: int | None = None


class SimpleScheduleUpdate(SimpleScheduleChange):
    task_name: str | None = None
    site_mode: int | None = None
    site_id: str | None = None
    work_mode: dict[str, Any] | None = None
    map_resource_list: list[dict[str, Any]] | None = None
    loop_count: int | None = None
    plan_execute_type: int | None = None
    plan_repeat_type: int | None = None
    plan_repeat_weekly: list[int] | None = None
    plan_start_time: str | None = None
    plan_stop_time: str | None = None
    task_advance_config: dict[str, Any] | None = None


@tool(name="update_simple_schedule", description="更新简易排班 / Update simple schedule", dangerous=True, category="schedules")
async def update_simple_schedule(v3, args: SimpleScheduleUpdate):
    return await v3.schedules.simple_update(**_body(args))


@tool(name="delete_simple_schedule", description="删除简易排班 / Delete simple schedule", dangerous=True, category="schedules")
async def delete_simple_schedule(v3, args: SimpleScheduleChange):
    return await v3.schedules.simple_delete(**args.model_dump())


class StandardSchedule(Robot):
    client_time_zone: str
    plan_execute_type: str | int
    plan_repeat_type: int
    plan_start_time: str
    semester_type: int
    task_name: str
    client_time: int | None = None
    plan_fusion_task_external: dict[str, Any] | None = None
    plan_fusion_task_main: dict[str, Any] | None = None
    plan_repeat_once: str | None = None
    plan_repeat_weekly: list[int] | None = None
    plan_start_date: str | None = None
    plan_stop_date: str | None = None
    plan_stop_time: str | None = None
    plan_uuid: str | None = None
    robot_sch_task_version: int | None = None


@tool(name="create_schedule", description="创建标准排班 / Create schedule", dangerous=True, category="schedules")
async def create_schedule(v3, args: StandardSchedule):
    return await v3.schedules.create(**_body(args))


class StandardUpdate(Robot):
    client_time_zone: str
    operation_type: int
    plan_execute_type: str | int
    plan_start_date: str
    plan_start_time: str
    plan_uuid: str
    semester_type: int
    semester_uuid: str
    client_time: int | None = None
    plan_commit_no: int | None = None
    plan_fusion_task_external: dict[str, Any] | None = None
    plan_fusion_task_main: dict[str, Any] | None = None
    plan_repeat_once: str | None = None
    plan_repeat_type: int | None = None
    plan_repeat_weekly: list[int] | None = None
    plan_stop_date: str | None = None
    plan_stop_time: str | None = None
    semester_commit_no: int | None = None
    task_name: str | None = None


@tool(name="update_schedule", description="更新标准排班 / Update schedule", dangerous=True, category="schedules")
async def update_schedule(v3, args: StandardUpdate):
    return await v3.schedules.update(**_body(args))


class StandardDelete(Robot):
    client_time_zone: str
    operation_type: int
    plan_start_date: str
    plan_uuid: str
    semester_uuid: str
    plan_commit_no: int | None = None
    semester_commit_no: int | None = None


@tool(name="delete_schedule", description="删除标准排班 / Delete schedule", dangerous=True, category="schedules")
async def delete_schedule(v3, args: StandardDelete):
    return await v3.schedules.delete(**args.model_dump())


@tool(name="list_schedules", description="列出排班 / List schedules", category="schedules")
async def list_schedules(v3, args: Robot):
    return await v3.schedules.list(args.robot_sn)


class ScheduleDetail(Robot):
    plan_uuid: str
    year: int
    month: int
    day_of_month: int


@tool(name="get_schedule", description="查询排班详情 / Get schedule", category="schedules")
async def get_schedule(v3, args: ScheduleDetail):
    return await v3.schedules.get(**args.model_dump())


class ScheduleMonth(Robot):
    year_month: str


@tool(name="get_schedule_calendar", description="查询月度排班 / Get schedule calendar", category="schedules")
async def get_schedule_calendar(v3, args: ScheduleMonth):
    try:
        year, month = (int(part) for part in args.year_month.split("-"))
        date(year, month, 1)
    except (ValueError, TypeError) as exc:
        raise ValueError("year_month must be YYYY-MM") from exc
    return await v3.schedules.get_calendar_month(args.robot_sn, year, month)


class ScheduleDate(Robot):
    date: str


@tool(name="list_schedule_pre_tasks", description="查询每日预任务 / List schedule pre-tasks", category="schedules")
async def list_schedule_pre_tasks(v3, args: ScheduleDate):
    try:
        day = date.fromisoformat(args.date)
    except ValueError as exc:
        raise ValueError("date must be YYYY-MM-DD") from exc
    return await v3.schedules.list_pre_tasks_day(args.robot_sn, day.year, day.month, day.day)


class CommandId(Robot):
    request_id: str


@tool(name="get_command_status", description="查询命令投递状态 / Get command delivery status", category="commands")
async def get_command_status(v3, args: CommandId):
    return await v3.commands.get_status(args.robot_sn, args.request_id)


class CommandHistory(Robot):
    page: int = 1
    pagesize: int = 20
    cmd_status: int | None = None
    command_type: str | None = None


@tool(name="list_command_history", description="查询命令历史 / List command history", category="commands")
async def list_command_history(v3, args: CommandHistory):
    return await v3.commands.page_history(args.robot_sn, args.page, args.pagesize,
                                          cmd_status=args.cmd_status, command_type=args.command_type)


class NavigateHome(RobotMap):
    map_resource_id: str | None = None


@tool(name="navigate_home", description="导航回充电点 / Navigate home", dangerous=True, category="commands")
async def navigate_home(v3, args: NavigateHome):
    return await v3.commands.navigation_go_home(**args.model_dump())


@tool(name="pause_navigation", description="暂停导航 / Pause navigation", dangerous=True, category="commands")
async def pause_navigation(v3, args: Robot):
    return await v3.commands.navigation_pause(args.robot_sn)


@tool(name="resume_navigation", description="继续导航 / Resume navigation", dangerous=True, category="commands")
async def resume_navigation(v3, args: Robot):
    return await v3.commands.navigation_resume(args.robot_sn)


@tool(name="stop_navigation", description="停止导航 / Stop navigation", dangerous=True, category="commands")
async def stop_navigation(v3, args: Robot):
    return await v3.commands.navigation_stop(args.robot_sn)


class Reports(Robot):
    page: int = 1
    pagesize: int = 20
    end_time_min: str | None = None
    end_time_max: str | None = None


@tool(name="list_task_reports", description="分页查询任务报告 / List task reports", category="reports")
async def list_task_reports(v3, args: Reports):
    return await v3.reports.page(**args.model_dump())


class ReportImages(Input):
    task_report_id: str
    robot_sn: str | None = None


@tool(name="get_task_report_map_images", description="查询报告地图图像 / Get report map images", category="reports")
async def get_task_report_map_images(v3, args: ReportImages):
    return await v3.reports.query_map_images(args.task_report_id, robot_sn=args.robot_sn)
