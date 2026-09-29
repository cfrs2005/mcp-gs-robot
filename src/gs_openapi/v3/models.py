"""
Pydantic v2 models for Gausium OpenAPI V3 responses.

All models use ``populate_by_name=True`` and ``extra="allow"`` so that they
parse the camelCase JSON returned by the API (via aliases) while exposing
snake_case Python attribute names. Field aliases match the exact field names
in the response examples of the official Gausium OpenAPI V3 documentation.
"""

from __future__ import annotations

import builtins
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _V3Model(BaseModel):
    """Base config for all V3 models: camelCase aliases, allow extras."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")


# ---------------------------------------------------------------------------
# Robot status snapshot (robots--get-robot-status-snapshot.md)
# ---------------------------------------------------------------------------
class GridPosition(_V3Model):
    x: float = Field(alias="x")
    y: float = Field(alias="y")


class MapInfo(_V3Model):
    grid_height: float = Field(alias="gridHeight")
    grid_width: float = Field(alias="gridWidth")
    origin_x: float = Field(alias="originX")
    origin_y: float = Field(alias="originY")
    resolution: float = Field(alias="resolution")


class Quaternion(_V3Model):
    w: float = Field(alias="w")
    x: float = Field(alias="x")
    y: float = Field(alias="y")
    z: float = Field(alias="z")


class Vector3(_V3Model):
    x: float = Field(alias="x")
    y: float = Field(alias="y")
    z: float = Field(alias="z")


class WorldPosition(_V3Model):
    orientation: Quaternion | None = Field(default=None, alias="orientation")
    position: Vector3 | None = Field(default=None, alias="position")


class RobotPosition(_V3Model):
    angle: float | None = Field(default=None, alias="angle")
    grid_position: GridPosition | None = Field(default=None, alias="gridPosition")
    map_info: MapInfo | None = Field(default=None, alias="mapInfo")
    world_position: WorldPosition | None = Field(default=None, alias="worldPosition")


class RobotStatusSnapshot(_V3Model):
    robot_sn: str = Field(alias="robotSn")
    battery_percent: int | None = Field(default=None, alias="batteryPercent")
    charging: bool | None = Field(default=None, alias="charging")
    current_map_id: str | None = Field(default=None, alias="currentMapId")
    current_map_name: str | None = Field(default=None, alias="currentMapName")
    observed_ms_timestamp: int | None = Field(
        default=None, alias="observedMsTimestamp"
    )
    online_status: str | None = Field(default=None, alias="onlineStatus")
    position: RobotPosition | None = Field(default=None, alias="position")
    task_instance_id: str | None = Field(default=None, alias="taskInstanceId")
    task_name: str | None = Field(default=None, alias="taskName")
    work_state: int | None = Field(default=None, alias="workState")


class RobotStatusPage(_V3Model):
    list: builtins.list[RobotStatusSnapshot] = Field(default_factory=list, alias="list")


# ---------------------------------------------------------------------------
# Robot maps (robot-maps--list-robot-maps.md)
# ---------------------------------------------------------------------------
class RobotMap(_V3Model):
    """All fields optional: some upstream environments omit ``mapId`` and only
    return ``displayName`` / ``mapVersionId`` / ``robotMapUuid``. There
    ``robotMapUuid`` carries the same value other endpoints report as ``mapId``
    (e.g. map-resource bundles), so ``map_id`` falls back to it."""

    display_name: str | None = Field(default=None, alias="displayName")
    map_id: str | None = Field(default=None, alias="mapId")
    map_version_id: str | None = Field(default=None, alias="mapVersionId")
    robot_map_uuid: str | None = Field(default=None, alias="robotMapUuid")

    @model_validator(mode="after")
    def _default_map_id(self) -> RobotMap:
        if self.map_id is None:
            self.map_id = self.robot_map_uuid
        return self


# ---------------------------------------------------------------------------
# Map canvas (robot-maps--get-robot-map-canvas.md)
# ---------------------------------------------------------------------------
class MapPng(_V3Model):
    download_uri: str | None = Field(default=None, alias="downloadUri")
    exist: bool | None = Field(default=None, alias="exist")


class MapCanvas(_V3Model):
    map_info: MapInfo | None = Field(default=None, alias="mapInfo")
    map_png: MapPng | None = Field(default=None, alias="mapPng")


# ---------------------------------------------------------------------------
# Charging positions (robot-maps--list-charging-positions.md)
# ---------------------------------------------------------------------------
class ChargingPosition(_V3Model):
    grid_x: Any | None = Field(default=None, alias="gridX")
    grid_y: Any | None = Field(default=None, alias="gridY")
    map_resource_id: str | None = Field(default=None, alias="mapResourceId")
    position_name: str | None = Field(default=None, alias="positionName")
    position_type: str | None = Field(default=None, alias="positionType")


class ChargingPositionList(_V3Model):
    map_id: str | None = Field(default=None, alias="mapId")
    positions: list[ChargingPosition] = Field(default_factory=list, alias="positions")
    robot_sn: str | None = Field(default=None, alias="robotSn")
    timestamp: Any | None = Field(default=None, alias="timestamp")


# ---------------------------------------------------------------------------
# Map resources (robot-maps--list-map-resources-without-work-modes.md,
# task-capability--capability-and-work-mode--list-schedule-map-resources.md)
# ---------------------------------------------------------------------------
class MapResource(_V3Model):
    map_resource_area_id: str | None = Field(default=None, alias="mapResourceAreaId")
    map_resource_id: str = Field(alias="mapResourceId")
    map_resource_name: str | None = Field(default=None, alias="mapResourceName")
    map_resource_type: str | None = Field(default=None, alias="mapResourceType")
    supported_actions: list[str] = Field(default_factory=list, alias="supportedActions")
    # Position-only fields (returned as strings in the docs).
    grid_x: Any | None = Field(default=None, alias="gridX")
    grid_y: Any | None = Field(default=None, alias="gridY")
    position_id: Any | None = Field(default=None, alias="positionId")
    position_type: Any | None = Field(default=None, alias="positionType")


class MapResourceMap(_V3Model):
    map_id: str = Field(alias="mapId")
    robot_map_uuid: str | None = Field(default=None, alias="robotMapUuid")
    paths: list[MapResource] = Field(default_factory=list, alias="paths")
    positions: list[MapResource] = Field(default_factory=list, alias="positions")
    regions: list[MapResource] = Field(default_factory=list, alias="regions")


class WorkMode(_V3Model):
    id: str | None = Field(default=None, alias="id")
    mode: str | None = Field(default=None, alias="mode")
    sub_type: str | None = Field(default=None, alias="subType")
    type: int | None = Field(default=None, alias="type")
    config_type: str | None = Field(default=None, alias="configType")
    default_strength: str | None = Field(default=None, alias="defaultStrength")
    has_strength: bool | None = Field(default=None, alias="hasStrength")
    recommended: bool | None = Field(default=None, alias="recommended")
    strength_options: list[str] = Field(default_factory=list, alias="strengthOptions")
    sub_task_enabled: bool | None = Field(default=None, alias="subTaskEnabled")


class MapResourceBundle(_V3Model):
    """Response of schedule-resources/list (maps + workModes + robotSn)."""

    maps: list[MapResourceMap] = Field(default_factory=list, alias="maps")
    work_modes: list[WorkMode] = Field(default_factory=list, alias="workModes")
    robot_sn: str | None = Field(default=None, alias="robotSn")


class MapResourceListResult(_V3Model):
    """Response of map-resources/list (maps + robotSn, no work modes)."""

    maps: list[MapResourceMap] = Field(default_factory=list, alias="maps")
    robot_sn: str | None = Field(default=None, alias="robotSn")


# ---------------------------------------------------------------------------
# Robot capabilities (task-capability--capability-and-work-mode--get-...md)
# ---------------------------------------------------------------------------
class RobotCapabilities(_V3Model):
    product_id: str | None = Field(default=None, alias="productId")
    robot_family_code: str | None = Field(default=None, alias="robotFamilyCode")
    support_fusion_task: int | None = Field(
        default=None, alias="supportFusionTask"
    )
    support_timer_schedule_task: int | None = Field(
        default=None, alias="supportTimerScheduleTask"
    )


# ---------------------------------------------------------------------------
# Command accepted / status / records
# ---------------------------------------------------------------------------
class CommandAccepted(_V3Model):
    """Returned by task start/pause/.../navigation commands."""

    request_id: str | None = Field(default=None, alias="requestId")
    cmd_status: int | None = Field(default=None, alias="cmdStatus")
    task_instance_id: str | None = Field(default=None, alias="taskInstanceId")


class CommandStatus(_V3Model):
    cmd_result_code: Any | None = Field(default=None, alias="cmdResultCode")
    cmd_result_message: str | None = Field(default=None, alias="cmdResultMessage")
    cmd_status: int | None = Field(default=None, alias="cmdStatus")
    command_type: str | None = Field(default=None, alias="commandType")
    request_id: str | None = Field(default=None, alias="requestId")
    robot_sn: str | None = Field(default=None, alias="robotSn")


class CommandRecord(_V3Model):
    cmd_result_code: Any | None = Field(default=None, alias="cmdResultCode")
    cmd_result_message: str | None = Field(default=None, alias="cmdResultMessage")
    cmd_status: int | None = Field(default=None, alias="cmdStatus")
    command_type: str | None = Field(default=None, alias="commandType")
    request_id: str | None = Field(default=None, alias="requestId")
    robot_sn: str | None = Field(default=None, alias="robotSn")
    task_instance_id: str | None = Field(default=None, alias="taskInstanceId")


class CommandRecordPage(_V3Model):
    list: builtins.list[CommandRecord] = Field(default_factory=list, alias="list")
    page_number: int | None = Field(default=None, alias="pageNumber")
    page_size: int | None = Field(default=None, alias="pageSize")
    total_size: int | None = Field(default=None, alias="totalSize")


# ---------------------------------------------------------------------------
# Task reports (task-capability--page-task-reports.md)
# ---------------------------------------------------------------------------
class ConsumablesResidual(_V3Model):
    # Measured upstream: fractional percentages (e.g. 87.5), so float not int.
    brush: float | None = Field(default=None, alias="brush")
    filter: float | None = Field(default=None, alias="filter")
    suction_blade: float | None = Field(default=None, alias="suctionBlade")


class SubTask(_V3Model):
    actual_cleaning_area_square_meter: float | None = Field(
        default=None, alias="actualCleaningAreaSquareMeter"
    )
    map_id: str | None = Field(default=None, alias="mapId")
    map_name: str | None = Field(default=None, alias="mapName")
    task_id: str | None = Field(default=None, alias="taskId")


class TaskReport(_V3Model):
    id: str | None = Field(default=None, alias="id")
    task_id: str | None = Field(default=None, alias="taskId")
    task_instance_id: str | None = Field(default=None, alias="taskInstanceId")
    task_report_png_uri: str | None = Field(
        default=None, alias="taskReportPngUri"
    )
    robot: str | None = Field(default=None, alias="robot")
    robot_serial_number: str | None = Field(
        default=None, alias="robotSerialNumber"
    )
    operator: str | None = Field(default=None, alias="operator")
    plan_id: str | None = Field(default=None, alias="planId")
    display_name: str | None = Field(default=None, alias="displayName")
    area_name_list: str | None = Field(default=None, alias="areaNameList")
    cleaning_mode: str | None = Field(default=None, alias="cleaningMode")
    start_time: int | None = Field(default=None, alias="startTime")
    end_time: int | None = Field(default=None, alias="endTime")
    # Percentages arrive as floats upstream (battery 81.0, completion 0.812 = ratio).
    start_battery_percentage: float | None = Field(
        default=None, alias="startBatteryPercentage"
    )
    end_battery_percentage: float | None = Field(
        default=None, alias="endBatteryPercentage"
    )
    duration_seconds: int | None = Field(default=None, alias="durationSeconds")
    plan_running_time: int | None = Field(default=None, alias="planRunningTime")
    completion_percentage: float | None = Field(
        default=None, alias="completionPercentage"
    )
    task_end_status: int | None = Field(default=None, alias="taskEndStatus")
    loop_count: int | None = Field(default=None, alias="loopCount")
    main_task_type: int | None = Field(default=None, alias="mainTaskType")
    task_start_type: int | None = Field(default=None, alias="taskStartType")
    task_trigger_source: int | None = Field(default=None, alias="taskTriggerSource")
    time_zone: int | None = Field(default=None, alias="timeZone")
    water_consumption_liter: float | None = Field(
        default=None, alias="waterConsumptionLiter"
    )
    actual_cleaning_area_square_meter: float | None = Field(
        default=None, alias="actualCleaningAreaSquareMeter"
    )
    planned_cleaning_area_square_meter: float | None = Field(
        default=None, alias="plannedCleaningAreaSquareMeter"
    )
    actual_polishing_area_square_meter: float | None = Field(
        default=None, alias="actualPolishingAreaSquareMeter"
    )
    planned_polishing_area_square_meter: float | None = Field(
        default=None, alias="plannedPolishingAreaSquareMeter"
    )
    efficiency_square_meter_per_hour: float | None = Field(
        default=None, alias="efficiencySquareMeterPerHour"
    )
    consumables_residual_percentage: ConsumablesResidual | None = Field(
        default=None, alias="consumablesResidualPercentage"
    )
    sub_tasks: list[SubTask] = Field(default_factory=list, alias="subTasks")


class TaskReportPage(_V3Model):
    count: int | None = Field(default=None, alias="count")
    page: int | None = Field(default=None, alias="page")
    pagesize: int | None = Field(default=None, alias="pagesize")
    robot_task_reports: list[TaskReport] = Field(
        default_factory=list, alias="robotTaskReports"
    )


# ---------------------------------------------------------------------------
# Task report map images (task-capability--query-task-report-map-images.md)
# ---------------------------------------------------------------------------
class TaskReportMapImage(_V3Model):
    map_image_id: int | None = Field(default=None, alias="map_image_id")
    product_id: str | None = Field(default=None, alias="product_id")
    task_queue_id: str | None = Field(default=None, alias="task_queue_id")
    url: str | None = Field(default=None, alias="url")


class TaskReportMapImageQuery(_V3Model):
    list: builtins.list[TaskReportMapImage] = Field(default_factory=list, alias="list")


# ---------------------------------------------------------------------------
# Persistent combined task definitions
# (task-capability--task-definition--*.md)
# ---------------------------------------------------------------------------
class TaskMapResource(_V3Model):
    map_id: str | None = Field(default=None, alias="mapId")
    map_resource_area_id: str | None = Field(
        default=None, alias="mapResourceAreaId"
    )
    map_resource_id: str | None = Field(default=None, alias="mapResourceId")
    map_resource_name: str | None = Field(
        default=None, alias="mapResourceName"
    )
    map_resource_type: str | None = Field(
        default=None, alias="mapResourceType"
    )


class TaskWorkMode(_V3Model):
    id: str | None = Field(default=None, alias="id")
    mode: str | None = Field(default=None, alias="mode")
    sub_type: str | None = Field(default=None, alias="subType")
    type: int | None = Field(default=None, alias="type")
    strength: str | None = Field(default=None, alias="strength")


class TaskAdvanceConfig(_V3Model):
    active_clean_mode: int | None = Field(default=None, alias="activeCleanMode")
    active_clean_switch: bool | None = Field(
        default=None, alias="activeCleanSwitch"
    )
    auto_planning: bool | None = Field(default=None, alias="autoPlanning")
    coverage_mode: str | None = Field(default=None, alias="coverageMode")
    sub_task_mode: bool | None = Field(default=None, alias="subTaskMode")
    task_running_mode: str | None = Field(
        default=None, alias="taskRunningMode"
    )
    temp_task_priority: bool | None = Field(
        default=None, alias="tempTaskPriority"
    )
    walking_pattern: Any | None = Field(default=None, alias="walkingPattern")


class FusionTaskDefinition(_V3Model):
    fusion_task_id: str | None = Field(default=None, alias="fusionTaskId")
    loop_count: int | None = Field(default=None, alias="loopCount")
    map_resource_list: list[TaskMapResource] = Field(
        default_factory=list, alias="mapResourceList"
    )
    robot_sn: str | None = Field(default=None, alias="robotSn")
    site_id: str | None = Field(default=None, alias="siteId")
    task_advance_config: TaskAdvanceConfig | None = Field(
        default=None, alias="taskAdvanceConfig"
    )
    task_name: str | None = Field(default=None, alias="taskName")
    work_mode: TaskWorkMode | None = Field(default=None, alias="workMode")


class FusionTaskDefinitionPage(_V3Model):
    list: builtins.list[FusionTaskDefinition] = Field(default_factory=list, alias="list")
    page_number: int | None = Field(default=None, alias="pageNumber")
    page_size: int | None = Field(default=None, alias="pageSize")
    total_size: int | None = Field(default=None, alias="totalSize")


# ---------------------------------------------------------------------------
# Schedule plans (schedule-task--*.md)
# ---------------------------------------------------------------------------
class SchedulePlanMapResource(_V3Model):
    map_resource_area_id: str | None = Field(
        default=None, alias="mapResourceAreaId"
    )
    map_resource_id: str | None = Field(default=None, alias="mapResourceId")
    map_resource_name: str | None = Field(
        default=None, alias="mapResourceName"
    )
    map_resource_type: str | None = Field(
        default=None, alias="mapResourceType"
    )


class SchedulePlanMap(_V3Model):
    floor_index: int | None = Field(default=None, alias="floorIndex")
    floor_name: str | None = Field(default=None, alias="floorName")
    map_id: str | None = Field(default=None, alias="mapId")
    map_name: str | None = Field(default=None, alias="mapName")
    map_resource_list: list[SchedulePlanMapResource] = Field(
        default_factory=list, alias="mapResourceList"
    )


class ScheduleFusionTaskExternal(_V3Model):
    fusion_task_id: str | None = Field(default=None, alias="fusionTaskId")
    fusion_task_type: int | None = Field(default=None, alias="fusionTaskType")
    map_list: list[SchedulePlanMap] = Field(default_factory=list, alias="mapList")
    site_id: str | None = Field(default=None, alias="siteId")
    site_name: str | None = Field(default=None, alias="siteName")
    task_api_version: str | None = Field(default=None, alias="taskAPIVersion")


class ScheduleSubTask(_V3Model):
    id: str | None = Field(default=None, alias="id")
    map_id: str | None = Field(default=None, alias="mapId")
    map_resource_id: str | None = Field(default=None, alias="mapResourceId")
    type: str | None = Field(default=None, alias="type")
    work_mode: TaskWorkMode | None = Field(default=None, alias="workMode")


class ScheduleFusionTaskMain(_V3Model):
    created_at: int | None = Field(default=None, alias="createdAt")
    fusion_name: str | None = Field(default=None, alias="fusionName")
    fusion_task_id: str | None = Field(default=None, alias="fusionTaskId")
    fusion_task_type: int | None = Field(default=None, alias="fusionTaskType")
    loop_count: int | None = Field(default=None, alias="loopCount")
    persistence: bool | None = Field(default=None, alias="persistence")
    related_task_id: str | None = Field(default=None, alias="relatedTaskId")
    site_info: dict | None = Field(default=None, alias="siteInfo")
    task_api_version: str | None = Field(default=None, alias="taskAPIVersion")
    task_advance_config: TaskAdvanceConfig | None = Field(
        default=None, alias="taskAdvanceConfig"
    )
    tasks: list[ScheduleSubTask] = Field(default_factory=list, alias="tasks")
    updated_at: int | None = Field(default=None, alias="updatedAt")
    updated_user: str | None = Field(default=None, alias="updatedUser")
    user: str | None = Field(default=None, alias="user")
    work_mode: TaskWorkMode | None = Field(default=None, alias="workMode")


class SchedulePlan(_V3Model):
    mission_status: int | None = Field(default=None, alias="missionStatus")
    plan_commit_no: Any | None = Field(default=None, alias="planCommitNo")
    plan_execute_type: str | None = Field(default=None, alias="planExecuteType")
    plan_fusion_task_external: ScheduleFusionTaskExternal | None = Field(
        default=None, alias="planFusionTaskExternal"
    )
    plan_fusion_task_main: ScheduleFusionTaskMain | None = Field(
        default=None, alias="planFusionTaskMain"
    )
    plan_repeat_once: str | None = Field(default=None, alias="planRepeatOnce")
    plan_repeat_type: int | None = Field(default=None, alias="planRepeatType")
    plan_repeat_weekly: list[int] = Field(
        default_factory=list, alias="planRepeatWeekly"
    )
    plan_start_date: str | None = Field(default=None, alias="planStartDate")
    plan_start_time: str | None = Field(default=None, alias="planStartTime")
    plan_stop_date: str | None = Field(default=None, alias="planStopDate")
    plan_stop_time: str | None = Field(default=None, alias="planStopTime")
    plan_uuid: str | None = Field(default=None, alias="planUuid")
    robot_sn: str | None = Field(default=None, alias="robotSn")
    semester_commit_no: Any | None = Field(
        default=None, alias="semesterCommitNo"
    )
    semester_type: int | None = Field(default=None, alias="semesterType")
    semester_uuid: str | None = Field(default=None, alias="semesterUuid")
    task_name: str | None = Field(default=None, alias="taskName")


class SchedulePlanList(_V3Model):
    """Wrapper for the list endpoint (data is an array of plans)."""

    plans: list[SchedulePlan] = Field(default_factory=list)

    @classmethod
    def from_list(cls, items: list) -> SchedulePlanList:
        return cls(plans=[SchedulePlan.model_validate(i) for i in items])


class RobotTimeZoneInfo(_V3Model):
    robot_sn: str | None = Field(default=None, alias="robotSn")
    robot_time_zone_type: str | None = Field(
        default=None, alias="robotTimeZoneType"
    )
    time_zone_id: str | None = Field(default=None, alias="timeZoneId")


class SchedulePreTaskDay(_V3Model):
    pre_tasks: list[SchedulePlan] = Field(default_factory=list, alias="preTasks")
    robot_time_zone_info: RobotTimeZoneInfo | None = Field(
        default=None, alias="robotTimeZoneInfo"
    )
    select_day: str | None = Field(default=None, alias="selectDay")


class ScheduleCalendarDay(_V3Model):
    day_of_month: int | None = Field(default=None, alias="dayOfMonth")
    exist_pre_tasks: int | None = Field(default=None, alias="existPreTasks")


class ScheduleCalendarMonth(_V3Model):
    day_list: list[ScheduleCalendarDay] = Field(
        default_factory=list, alias="dayList"
    )
    month: int | None = Field(default=None, alias="month")
    year: int | None = Field(default=None, alias="year")


class SimpleSchedulePlanResult(_V3Model):
    """Result of simple schedule create (contains planUuid)."""

    plan_commit_no: Any | None = Field(default=None, alias="planCommitNo")
    plan_uuid: str | None = Field(default=None, alias="planUuid")
    robot_sn: str | None = Field(default=None, alias="robotSn")
    semester_commit_no: Any | None = Field(
        default=None, alias="semesterCommitNo"
    )
    semester_uuid: str | None = Field(default=None, alias="semesterUuid")
