"""
:class:`GausiumV3` — typed async facade for the Gausium OpenAPI V3 business
endpoints.

Each method maps Python snake_case keyword arguments to the exact camelCase
request fields documented in ``docs/openapi-v3/*.md`` and returns a parsed
pydantic model (for query endpoints) or a ``dict`` (for mutation endpoints).
The facade delegates HTTP, envelope unwrapping, and 401-retry to
:class:`gs_openapi.core.client.GausiumAPIClient.call_v3`.
"""

from __future__ import annotations

import builtins
from typing import Any

from ..core.client import GausiumAPIClient
from .models import (
    ChargingPositionList,
    CommandAccepted,
    CommandRecordPage,
    CommandStatus,
    FusionTaskDefinition,
    FusionTaskDefinitionPage,
    MapCanvas,
    MapResourceBundle,
    MapResourceListResult,
    RobotCapabilities,
    RobotMap,
    RobotStatusPage,
    RobotStatusSnapshot,
    ScheduleCalendarMonth,
    SchedulePlan,
    SchedulePreTaskDay,
    SimpleSchedulePlanResult,
    TaskReportMapImageQuery,
    TaskReportPage,
    WorkMode,
)


def _clean(body: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is ``None``."""
    return {k: v for k, v in body.items() if v is not None}


class _RobotsNamespace:
    def __init__(self, facade: GausiumV3) -> None:
        self._facade = facade

    async def get_status(self, robot_sn_list: list[str]) -> RobotStatusPage:
        """Get robot status snapshots. Doc: robots--get-robot-status-snapshot.md"""
        data = await self._facade._call("v3_robots_status_get", {"robotSnList": robot_sn_list})
        return RobotStatusPage.model_validate(data)

    async def get_one_status(self, robot_sn: str) -> RobotStatusSnapshot | None:
        """Convenience wrapper: fetch a single robot's status snapshot."""
        page = await self.get_status([robot_sn])
        for snap in page.list:
            if snap.robot_sn == robot_sn:
                return snap
        return page.list[0] if page.list else None


class _MapsNamespace:
    def __init__(self, facade: GausiumV3) -> None:
        self._facade = facade

    async def list_maps(self, robot_sn: str) -> list[RobotMap]:
        """List robot maps. Doc: robot-maps--list-robot-maps.md"""
        data = await self._facade._call("v3_robots_maps_list", {"robotSn": robot_sn})
        return [RobotMap.model_validate(m) for m in data] if isinstance(data, list) else []

    async def get_canvas(self, robot_sn: str, map_id: str) -> MapCanvas:
        """Get map canvas PNG + metadata. Doc: robot-maps--get-robot-map-canvas.md"""
        data = await self._facade._call(
            "v3_robots_maps_canvas_get", {"robotSn": robot_sn, "mapId": map_id}
        )
        return MapCanvas.model_validate(data)

    async def list_charging_positions(
        self, robot_sn: str, map_id: str
    ) -> ChargingPositionList:
        """List charging positions. Doc: robot-maps--list-charging-positions.md"""
        data = await self._facade._call(
            "v3_maps_charging_positions_list", {"robotSn": robot_sn, "mapId": map_id}
        )
        return ChargingPositionList.model_validate(data)

    async def list_resources(
        self,
        robot_sn: str,
        map_id_list: list[str],
        *,
        include_paths: bool | None = None,
        include_regions: bool | None = None,
        include_positions: bool | None = None,
    ) -> MapResourceListResult:
        """List map resources without work modes. Doc: robot-maps--list-map-resources-without-work-modes.md"""
        data = await self._facade._call(
            "v3_maps_resources_list",
            _clean(
                {
                    "robotSn": robot_sn,
                    "mapIdList": map_id_list,
                    "includePaths": include_paths,
                    "includeRegions": include_regions,
                    "includePositions": include_positions,
                }
            ),
        )
        return MapResourceListResult.model_validate(data)

    async def list_schedule_resources(
        self,
        robot_sn: str,
        map_id_list: list[str],
        *,
        include_paths: bool | None = None,
        include_regions: bool | None = None,
        include_positions: bool | None = None,
    ) -> MapResourceBundle:
        """List task resources (work modes + maps). Doc: task-capability--capability-and-work-mode--list-schedule-map-resources.md"""
        data = await self._facade._call(
            "v3_maps_schedule_resources_list",
            _clean(
                {
                    "robotSn": robot_sn,
                    "mapIdList": map_id_list,
                    "includePaths": include_paths,
                    "includeRegions": include_regions,
                    "includePositions": include_positions,
                }
            ),
        )
        return MapResourceBundle.model_validate(data)


class _TasksNamespace:
    def __init__(self, facade: GausiumV3) -> None:
        self._facade = facade

    async def get_capabilities(self, robot_sn: str) -> RobotCapabilities:
        """Get robot combined task capabilities. Doc: task-capability--capability-and-work-mode--get-robot-combined-task-capabilities.md"""
        data = await self._facade._call(
            "v3_tasks_capabilities_get", {"robotSn": robot_sn}
        )
        return RobotCapabilities.model_validate(data)

    async def list_work_modes(self, robot_sn: str) -> list[WorkMode]:
        """List robot work modes. Doc: task-capability--capability-and-work-mode--query-robot-work-modes.md"""
        data = await self._facade._call(
            "v3_tasks_work_modes_list", {"robotSn": robot_sn}
        )
        return [WorkMode.model_validate(w) for w in data] if isinstance(data, list) else []

    async def create_definition(
        self,
        *,
        robot_sn: str,
        task_name: str,
        map_resource_list: list[dict[str, Any]],
        work_mode: dict[str, Any],
        loop_count: int | None = None,
        site_id: str | None = None,
        task_advance_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a persistent combined task definition. Doc: task-capability--task-definition--create-...md"""
        return await self._facade._call(
            "v3_tasks_definitions_create",
            _clean(
                {
                    "robotSn": robot_sn,
                    "taskName": task_name,
                    "mapResourceList": map_resource_list,
                    "workMode": work_mode,
                    "loopCount": loop_count,
                    "siteId": site_id,
                    "taskAdvanceConfig": task_advance_config,
                }
            ),
        )

    async def update_definition(
        self,
        *,
        robot_sn: str,
        fusion_task_id: str,
        task_name: str | None = None,
        map_resource_list: list[dict[str, Any]] | None = None,
        work_mode: dict[str, Any] | None = None,
        loop_count: int | None = None,
        site_id: str | None = None,
        task_advance_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a persistent combined task definition. Doc: task-capability--task-definition--update-...md"""
        return await self._facade._call(
            "v3_tasks_definitions_update",
            _clean(
                {
                    "robotSn": robot_sn,
                    "fusionTaskId": fusion_task_id,
                    "taskName": task_name,
                    "mapResourceList": map_resource_list,
                    "workMode": work_mode,
                    "loopCount": loop_count,
                    "siteId": site_id,
                    "taskAdvanceConfig": task_advance_config,
                }
            ),
        )

    async def delete_definition(
        self, robot_sn: str, fusion_task_id: str
    ) -> dict[str, Any]:
        """Delete a persistent combined task definition. Doc: task-capability--task-definition--delete-...md"""
        return await self._facade._call(
            "v3_tasks_definitions_delete",
            {"robotSn": robot_sn, "fusionTaskId": fusion_task_id},
        )

    async def get_definition(
        self, robot_sn: str, fusion_task_id: str
    ) -> FusionTaskDefinition:
        """Get a persistent combined task definition. Doc: task-capability--task-definition--get-...md"""
        data = await self._facade._call(
            "v3_tasks_definitions_get",
            {"robotSn": robot_sn, "fusionTaskId": fusion_task_id},
        )
        return FusionTaskDefinition.model_validate(data)

    async def page_definitions(
        self,
        robot_sn: str,
        page_number: int,
        page_size: int,
        *,
        site_id: str | None = None,
        task_name: str | None = None,
    ) -> FusionTaskDefinitionPage:
        """Page persistent combined task definitions. Doc: task-capability--task-definition--page-...md"""
        data = await self._facade._call(
            "v3_tasks_definitions_page",
            _clean(
                {
                    "robotSn": robot_sn,
                    "pageNumber": page_number,
                    "pageSize": page_size,
                    "siteId": site_id,
                    "taskName": task_name,
                }
            ),
        )
        return FusionTaskDefinitionPage.model_validate(data)

    async def start(
        self,
        robot_sn: str,
        fusion_task_id: str,
        *,
        loop_count: int | None = None,
    ) -> CommandAccepted:
        """Start a combined task. Doc: temporary-task--start-a-combined-task.md"""
        data = await self._facade._call(
            "v3_tasks_start",
            _clean(
                {
                    "robotSn": robot_sn,
                    "fusionTaskId": fusion_task_id,
                    "loopCount": loop_count,
                }
            ),
        )
        return CommandAccepted.model_validate(data)

    async def pause(self, robot_sn: str) -> CommandAccepted:
        """Pause the current task. Doc: temporary-task--pause-the-current-task.md"""
        data = await self._facade._call("v3_tasks_pause", {"robotSn": robot_sn})
        return CommandAccepted.model_validate(data)

    async def resume(self, robot_sn: str) -> CommandAccepted:
        """Resume the current task. Doc: temporary-task--resume-the-current-task.md"""
        data = await self._facade._call("v3_tasks_resume", {"robotSn": robot_sn})
        return CommandAccepted.model_validate(data)

    async def stop(self, robot_sn: str) -> CommandAccepted:
        """Stop the current task. Doc: temporary-task--stop-the-current-task.md"""
        data = await self._facade._call("v3_tasks_stop", {"robotSn": robot_sn})
        return CommandAccepted.model_validate(data)

    async def skip(self, robot_sn: str) -> CommandAccepted:
        """Skip the current task item. Doc: temporary-task--skip-the-current-task-item.md"""
        data = await self._facade._call("v3_tasks_skip", {"robotSn": robot_sn})
        return CommandAccepted.model_validate(data)


class _SchedulesNamespace:
    def __init__(self, facade: GausiumV3) -> None:
        self._facade = facade

    async def simple_create(self, **body: Any) -> SimpleSchedulePlanResult:
        """Create a simple schedule plan. Doc: schedule-task--simple-schedule--create-simple-schedule-plan.md

        Callers pass the exact camelCase request fields as keyword arguments
        (e.g. ``robot_sn=...`` mapped via ``_clean`` is not applied here; pass
        already-camelCase keys such as ``robotSn=..., planExecuteType=2, ...``).
        """
        data = await self._facade._call("v3_schedules_simple_create", body)
        return SimpleSchedulePlanResult.model_validate(data)

    async def simple_update(self, **body: Any) -> dict[str, Any]:
        """Update a simple schedule plan. Doc: schedule-task--simple-schedule--update-simple-schedule-plan.md"""
        return await self._facade._call("v3_schedules_simple_update", body)

    async def simple_delete(
        self,
        *,
        robot_sn: str,
        plan_uuid: str,
        year: int,
        month: int,
        day_of_month: int,
        operation_type: int,
        client_time_zone: str | None = None,
        client_time: int | None = None,
    ) -> dict[str, Any]:
        """Delete a simple schedule plan. Doc: schedule-task--simple-schedule--delete-simple-schedule-plan.md"""
        return await self._facade._call(
            "v3_schedules_simple_delete",
            _clean(
                {
                    "robotSn": robot_sn,
                    "planUuid": plan_uuid,
                    "year": year,
                    "month": month,
                    "dayOfMonth": day_of_month,
                    "operationType": operation_type,
                    "clientTimeZone": client_time_zone,
                    "clientTime": client_time,
                }
            ),
        )

    async def create(self, **body: Any) -> dict[str, Any]:
        """Create a standard schedule plan. Doc: schedule-task--standard-schedule--create-schedule-plan.md"""
        return await self._facade._call("v3_schedules_create", body)

    async def update(self, **body: Any) -> dict[str, Any]:
        """Update a standard schedule plan. Doc: schedule-task--standard-schedule--update-schedule-plan.md"""
        return await self._facade._call("v3_schedules_update", body)

    async def delete(
        self,
        *,
        robot_sn: str,
        plan_uuid: str,
        plan_start_date: str,
        operation_type: int,
        semester_uuid: str,
        client_time_zone: str = "Asia/Shanghai",
        plan_commit_no: Any | None = None,
        semester_commit_no: Any | None = None,
    ) -> dict[str, Any]:
        """Delete a standard schedule plan. Doc: schedule-task--standard-schedule--delete-schedule-plan.md"""
        return await self._facade._call(
            "v3_schedules_delete",
            _clean(
                {
                    "robotSn": robot_sn,
                    "planUuid": plan_uuid,
                    "planStartDate": plan_start_date,
                    "operationType": operation_type,
                    "semesterUuid": semester_uuid,
                    "clientTimeZone": client_time_zone,
                    "planCommitNo": plan_commit_no,
                    "semesterCommitNo": semester_commit_no,
                }
            ),
        )

    async def list(self, robot_sn: str) -> builtins.list[SchedulePlan]:
        """List all schedule plans for a robot. Doc: schedule-task--standard-schedule--list-schedule-plans.md"""
        data = await self._facade._call("v3_schedules_list", {"robotSn": robot_sn})
        return [SchedulePlan.model_validate(p) for p in data] if isinstance(data, list) else []

    async def get(
        self, robot_sn: str, year: int, month: int, day_of_month: int, plan_uuid: str
    ) -> SchedulePlan:
        """Get a schedule plan detail. Doc: schedule-task--standard-schedule--query-schedule-plan-detail.md"""
        data = await self._facade._call(
            "v3_schedules_get",
            {
                "robotSn": robot_sn,
                "year": year,
                "month": month,
                "dayOfMonth": day_of_month,
                "planUuid": plan_uuid,
            },
        )
        return SchedulePlan.model_validate(data)

    async def list_pre_tasks_day(
        self, robot_sn: str, year: int, month: int, day_of_month: int
    ) -> SchedulePreTaskDay:
        """List schedule pre-tasks for a day. Doc: schedule-task--standard-schedule--list-schedule-pre-tasks-by-day.md"""
        data = await self._facade._call(
            "v3_schedules_pre_tasks_day_list",
            {
                "robotSn": robot_sn,
                "year": year,
                "month": month,
                "dayOfMonth": day_of_month,
            },
        )
        return SchedulePreTaskDay.model_validate(data)

    async def get_calendar_month(
        self, robot_sn: str, year: int, month: int
    ) -> ScheduleCalendarMonth:
        """Get monthly schedule calendar. Doc: schedule-task--standard-schedule--query-schedule-calendar-by-month.md"""
        data = await self._facade._call(
            "v3_schedules_calendar_month_get",
            {"robotSn": robot_sn, "year": year, "month": month},
        )
        return ScheduleCalendarMonth.model_validate(data)


class _CommandsNamespace:
    def __init__(self, facade: GausiumV3) -> None:
        self._facade = facade

    async def get_status(self, robot_sn: str, request_id: str) -> CommandStatus:
        """Get command delivery status. Doc: command-operation--get-command-delivery-status.md"""
        data = await self._facade._call(
            "v3_commands_status_get",
            {"robotSn": robot_sn, "requestId": request_id},
        )
        return CommandStatus.model_validate(data)

    async def page_history(
        self,
        robot_sn: str,
        page_number: int,
        page_size: int,
        *,
        cmd_status: int | None = None,
        command_type: str | None = None,
    ) -> CommandRecordPage:
        """Page command delivery history. Doc: command-operation--page-command-delivery-history.md"""
        data = await self._facade._call(
            "v3_commands_history_page",
            _clean(
                {
                    "robotSn": robot_sn,
                    "pageNumber": page_number,
                    "pageSize": page_size,
                    "cmdStatus": cmd_status,
                    "commandType": command_type,
                }
            ),
        )
        return CommandRecordPage.model_validate(data)

    async def navigation_go_home(
        self,
        robot_sn: str,
        map_id: str,
        *,
        map_resource_id: str | None = None,
    ) -> CommandAccepted:
        """Navigate robot to a charging position. Doc: command-operation--navigate-to-a-charging-position.md"""
        data = await self._facade._call(
            "v3_commands_navigation_go_home",
            _clean(
                {
                    "robotSn": robot_sn,
                    "mapId": map_id,
                    "mapResourceId": map_resource_id,
                }
            ),
        )
        return CommandAccepted.model_validate(data)

    async def navigation_pause(self, robot_sn: str) -> CommandAccepted:
        """Pause the current navigation. Doc: command-operation--pause-the-current-navigation.md"""
        data = await self._facade._call(
            "v3_commands_navigation_pause", {"robotSn": robot_sn}
        )
        return CommandAccepted.model_validate(data)

    async def navigation_resume(self, robot_sn: str) -> CommandAccepted:
        """Resume the current navigation. Doc: command-operation--resume-the-current-navigation.md"""
        data = await self._facade._call(
            "v3_commands_navigation_resume", {"robotSn": robot_sn}
        )
        return CommandAccepted.model_validate(data)

    async def navigation_stop(self, robot_sn: str) -> CommandAccepted:
        """Stop the current navigation. Doc: command-operation--stop-the-current-navigation.md"""
        data = await self._facade._call(
            "v3_commands_navigation_stop", {"robotSn": robot_sn}
        )
        return CommandAccepted.model_validate(data)


class _ReportsNamespace:
    def __init__(self, facade: GausiumV3) -> None:
        self._facade = facade

    async def page(
        self,
        robot_sn: str,
        page: int,
        *,
        pagesize: int | None = None,
        end_time_min: str | None = None,
        end_time_max: str | None = None,
    ) -> TaskReportPage:
        """Page task reports. Doc: task-capability--page-task-reports.md"""
        data = await self._facade._call(
            "v3_reports_page",
            _clean(
                {
                    "robotSn": robot_sn,
                    "page": page,
                    "pagesize": pagesize,
                    "endTimeMin": end_time_min,
                    "endTimeMax": end_time_max,
                }
            ),
        )
        return TaskReportPage.model_validate(data)

    async def query_map_images(
        self, task_report_id: str, *, robot_sn: str | None = None
    ) -> TaskReportMapImageQuery:
        """Query task report map images. Doc: task-capability--query-task-report-map-images.md"""
        data = await self._facade._call(
            "v3_reports_map_images_query",
            _clean(
                {
                    "taskReportId": task_report_id,
                    "robotSn": robot_sn,
                }
            ),
        )
        return TaskReportMapImageQuery.model_validate(data)


class GausiumV3:
    """
    Typed async facade for Gausium OpenAPI V3.

    Usage::

        async with GausiumAPIClient() as client:
            v3 = GausiumV3(client)
            page = await v3.robots.get_status(["GS123-..."])
            print(page.list[0].work_state)

    The facade exposes six namespaces — :attr:`robots`, :attr:`maps`,
    :attr:`tasks`, :attr:`schedules`, :attr:`commands`, :attr:`reports` — each
    with typed async methods covering one V3 business endpoint.
    """

    def __init__(self, client: GausiumAPIClient) -> None:
        self._client = client
        self.robots = _RobotsNamespace(self)
        self.maps = _MapsNamespace(self)
        self.tasks = _TasksNamespace(self)
        self.schedules = _SchedulesNamespace(self)
        self.commands = _CommandsNamespace(self)
        self.reports = _ReportsNamespace(self)

    async def _call(self, endpoint_name: str, body: dict[str, Any]) -> Any:
        """Delegate to the underlying client's V3 call."""
        return await self._client.call_v3(endpoint_name, body)
