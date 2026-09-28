"""
Tests for gs_openapi.v3.models — parsing the response examples from the docs
for RobotStatusSnapshot, MapResourceBundle, and TaskReportPage.
"""

import pytest

from gs_openapi.v3.models import (
    MapResourceBundle,
    RobotStatusPage,
    RobotStatusSnapshot,
    TaskReportPage,
)


ROBOT_STATUS_EXAMPLE = {
    "list": [
        {
            "batteryPercent": 27,
            "charging": False,
            "currentMapId": "66b5ea58-353e-41ee-bd6a-e959b2e27e25",
            "currentMapName": "0818一楼大厅",
            "observedMsTimestamp": 1788226978000,
            "onlineStatus": "ONLINE",
            "position": {
                "angle": -175.96,
                "gridPosition": {"x": 361, "y": 345},
                "mapInfo": {
                    "gridHeight": 748,
                    "gridWidth": 489,
                    "originX": -21.5,
                    "originY": -21.1,
                    "resolution": 0.05,
                },
                "worldPosition": {
                    "orientation": {"w": -0.035, "x": 0, "y": 0, "z": 0.999},
                    "position": {"x": -3.408, "y": -3.841, "z": 0},
                },
            },
            "robotSn": "TEST00-0000-000-S096",
            "taskInstanceId": "eeca9fe6-281f-41f8-8d03-6824d922ebf3",
            "taskName": "每日清扫任务",
            "workState": 230,
        },
        {
            "charging": True,
            "currentMapId": "420b2843-f3c6-4045-8f1c-8499940ed776",
            "currentMapName": "大堂地图",
            "observedMsTimestamp": 1788226967000,
            "onlineStatus": "ONLINE",
            "robotSn": "SIM00-0000-000-B011",
            "workState": 100,
        },
        {"onlineStatus": "OFFLINE", "robotSn": "TEST00-0000-000-S014"},
    ]
}


def test_robot_status_snapshot_parsing():
    page = RobotStatusPage.model_validate(ROBOT_STATUS_EXAMPLE)
    assert len(page.list) == 3
    s0 = page.list[0]
    assert s0.robot_sn == "TEST00-0000-000-S096"
    assert s0.battery_percent == 27
    assert s0.work_state == 230
    assert s0.position is not None
    assert s0.position.angle == -175.96
    assert s0.position.grid_position.x == 361
    assert s0.position.grid_position.y == 345
    assert s0.position.map_info.resolution == 0.05
    assert s0.position.world_position.orientation.z == 0.999
    assert s0.position.world_position.position.x == -3.408
    # Sparse snapshot parses with optionals as None.
    s2 = page.list[2]
    assert s2.robot_sn == "TEST00-0000-000-S014"
    assert s2.online_status == "OFFLINE"
    assert s2.position is None
    assert s2.work_state is None


MAP_RESOURCE_BUNDLE_EXAMPLE = {
    "maps": [
        {
            "mapId": "0d33e11c-f29c-4294-b56b-e8829f2e2286",
            "paths": [
                {
                    "mapResourceId": "f2c36954-000b-416d-a011-2ba1edebdc12",
                    "mapResourceName": "Recorded Path 1",
                    "mapResourceType": "path",
                    "supportedActions": ["sweep"],
                }
            ],
            "positions": [
                {
                    "gridX": "341",
                    "gridY": "397",
                    "mapResourceAreaId": "",
                    "mapResourceId": "ab7d7f84-725d-4e99-a75d-b3055e794d73",
                    "mapResourceName": "Navigation Point 1",
                    "mapResourceType": "position",
                    "positionId": "0",
                    "positionType": "2",
                    "supportedActions": ["sweep"],
                }
            ],
            "regions": [
                {
                    "mapResourceAreaId": "3",
                    "mapResourceId": "1fa90e86-3e51-4d31-8dad-285ad6e5a072",
                    "mapResourceName": "area3",
                    "mapResourceType": "region",
                    "supportedActions": ["sweep"],
                }
            ],
            "robotMapUuid": "0d33e11c-f29c-4294-b56b-e8829f2e2286",
        }
    ],
    "robotSn": "TEST00-0000-000-S014",
    "workModes": [
        {
            "configType": "strength",
            "defaultStrength": "middle",
            "hasStrength": True,
            "id": "09f32e0e25154338ad149cbff97f8c4b",
            "mode": "sweep",
            "recommended": True,
            "strengthOptions": ["low", "middle", "high"],
            "subTaskEnabled": True,
            "subType": "sweep",
            "type": 0,
        }
    ],
}


def test_map_resource_bundle_parsing():
    bundle = MapResourceBundle.model_validate(MAP_RESOURCE_BUNDLE_EXAMPLE)
    assert bundle.robot_sn == "TEST00-0000-000-S014"
    assert len(bundle.maps) == 1
    m = bundle.maps[0]
    assert m.map_id == "0d33e11c-f29c-4294-b56b-e8829f2e2286"
    assert m.robot_map_uuid == m.map_id
    assert len(m.regions) == 1
    assert m.regions[0].map_resource_type == "region"
    assert m.regions[0].map_resource_area_id == "3"
    assert len(m.paths) == 1
    assert m.paths[0].map_resource_name == "Recorded Path 1"
    assert len(m.positions) == 1
    assert m.positions[0].grid_x == "341"
    assert m.positions[0].position_type == "2"
    assert len(bundle.work_modes) == 1
    wm = bundle.work_modes[0]
    assert wm.mode == "sweep"
    assert wm.has_strength is True
    assert wm.strength_options == ["low", "middle", "high"]


TASK_REPORT_PAGE_EXAMPLE = {
    "count": 1,
    "page": 1,
    "pagesize": 20,
    "robotTaskReports": [
        {
            "actualCleaningAreaSquareMeter": 0,
            "areaNameList": "",
            "cleaningMode": "",
            "completionPercentage": 0,
            "consumablesResidualPercentage": {
                "brush": 0, "filter": 0, "suctionBlade": 0,
            },
            "durationSeconds": 0,
            "endTime": 0,
            "id": "rep-1",
            "robotSerialNumber": "R1",
            "startTime": 0,
            "subTasks": [
                {
                    "actualCleaningAreaSquareMeter": 0,
                    "mapId": "m1", "mapName": "Lobby", "taskId": "t1",
                }
            ],
            "taskEndStatus": 0,
            "taskId": "t1",
            "taskInstanceId": "ti-1",
        }
    ],
}


def test_task_report_page_parsing():
    page = TaskReportPage.model_validate(TASK_REPORT_PAGE_EXAMPLE)
    assert page.count == 1
    assert page.page == 1
    assert page.pagesize == 20
    assert len(page.robot_task_reports) == 1
    rep = page.robot_task_reports[0]
    assert rep.id == "rep-1"
    assert rep.robot_serial_number == "R1"
    assert rep.consumables_residual_percentage is not None
    assert rep.consumables_residual_percentage.brush == 0
    assert len(rep.sub_tasks) == 1
    assert rep.sub_tasks[0].map_name == "Lobby"


def test_extra_fields_allowed():
    # The API may return undocumented fields; extra="allow" keeps them.
    snap = RobotStatusSnapshot.model_validate(
        {"robotSn": "R1", "futureField": 42}
    )
    assert snap.robot_sn == "R1"
    # Extra fields are retained on the model instance.
    assert snap.model_dump().get("futureField") == 42 or "futureField" in snap.__pydantic_extra__
