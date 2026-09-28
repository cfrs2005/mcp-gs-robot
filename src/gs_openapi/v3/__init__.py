"""
Gausium OpenAPI V3 typed async client package.

This package provides:

* :mod:`gs_openapi.v3.models` — pydantic v2 models for V3 responses.
* :mod:`gs_openapi.v3.references` — work-state, command-type, and task-error
  reference tables and helpers.
* :mod:`gs_openapi.v3.api` — the :class:`GausiumV3` facade with typed async
  methods for every V3 business endpoint.
"""

from .api import GausiumV3
from .models import (
    ChargingPosition,
    ChargingPositionList,
    CommandAccepted,
    CommandRecord,
    CommandRecordPage,
    CommandStatus,
    FusionTaskDefinition,
    FusionTaskDefinitionPage,
    MapCanvas,
    MapResource,
    MapResourceBundle,
    RobotCapabilities,
    RobotMap,
    RobotStatusPage,
    RobotStatusSnapshot,
    ScheduleCalendarMonth,
    SchedulePlan,
    SchedulePlanList,
    SchedulePreTaskDay,
    SimpleSchedulePlanResult,
    TaskReport,
    TaskReportMapImage,
    TaskReportMapImageQuery,
    TaskReportPage,
    WorkMode,
)
from .references import (
    COMMAND_TYPES,
    TASK_START_ERROR_CODES,
    WORK_STATES,
    describe_task_error,
    describe_work_state,
    is_terminal_work_state,
)

__all__ = [
    "COMMAND_TYPES",
    "TASK_START_ERROR_CODES",
    "WORK_STATES",
    "ChargingPosition",
    "ChargingPositionList",
    "CommandAccepted",
    "CommandRecord",
    "CommandRecordPage",
    "CommandStatus",
    "FusionTaskDefinition",
    "FusionTaskDefinitionPage",
    "GausiumV3",
    "MapCanvas",
    "MapResource",
    "MapResourceBundle",
    "RobotCapabilities",
    "RobotMap",
    "RobotStatusPage",
    "RobotStatusSnapshot",
    "ScheduleCalendarMonth",
    "SchedulePlan",
    "SchedulePlanList",
    "SchedulePreTaskDay",
    "SimpleSchedulePlanResult",
    "TaskReport",
    "TaskReportMapImage",
    "TaskReportMapImageQuery",
    "TaskReportPage",
    "WorkMode",
    "describe_task_error",
    "describe_work_state",
    "is_terminal_work_state",
]
