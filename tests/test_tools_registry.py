"""Contract checks for the shared V3 tool registry."""

import json

import httpx
import pytest

from gs_openapi.auth.token_manager import TokenManager
from gs_openapi.core.client import GausiumAPIClient
from gs_openapi.tools.registry import (
    REGISTRY,
    ToolInputError,
    invoke,
    to_anthropic_tools,
    to_openai_tools,
)
from gs_openapi.v3.api import GausiumV3

EXPECTED = [
    "list_robots", "get_robot_status", "describe_work_state", "get_robot_capabilities",
    "list_robot_maps", "get_map_canvas", "list_charging_positions", "list_map_resources",
    "list_task_resources", "list_work_modes", "list_task_definitions", "get_task_definition",
    "create_task_definition", "update_task_definition", "delete_task_definition", "start_task",
    "pause_task", "resume_task", "stop_task", "skip_task_item",
    "create_simple_schedule", "update_simple_schedule", "delete_simple_schedule",
    "create_schedule", "update_schedule", "delete_schedule", "list_schedules", "get_schedule",
    "get_schedule_calendar", "list_schedule_pre_tasks", "get_command_status",
    "list_command_history", "navigate_home", "pause_navigation", "resume_navigation",
    "stop_navigation", "list_task_reports", "get_task_report_map_images",
    "run_cleaning_task", "wait_for_command", "lookup_error_code", "remember",
]
MUTATIONS = {
    "create_task_definition", "update_task_definition", "delete_task_definition", "start_task",
    "pause_task", "resume_task", "stop_task", "skip_task_item",
    "create_simple_schedule", "update_simple_schedule", "delete_simple_schedule",
    "create_schedule", "update_schedule", "delete_schedule", "navigate_home",
    "pause_navigation", "resume_navigation", "stop_navigation", "run_cleaning_task", "remember",
}


def test_registry_and_schemas():
    assert set(REGISTRY) == set(EXPECTED)
    assert len(REGISTRY) == len(EXPECTED)
    assert {name for name, spec in REGISTRY.items() if spec.dangerous} == MUTATIONS
    for anthropic, openai in zip(to_anthropic_tools(), to_openai_tools()):
        assert anthropic["input_schema"]["additionalProperties"] is False
        assert "title" not in str(anthropic["input_schema"])
        assert openai["function"]["parameters"] == anthropic["input_schema"]
    assert "map_id" in REGISTRY["navigate_home"].input_model.model_fields
    assert "task_report_id" in REGISTRY["get_task_report_map_images"].input_model.model_fields


async def test_invoke_validation():
    with pytest.raises(ToolInputError, match="robot_sn_list"):
        await invoke("get_robot_status", {"robot_sn_list": ["R"] * 101}, None)
    with pytest.raises(ToolInputError, match="robot_sn"):
        await invoke("start_task", {"fusion_task_id": "x"}, None)


def _mock_v3(handler):
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token = TokenManager(client_id="c", client_secret="s", open_access_key="k",
                         http_client=http_client)
    return GausiumV3(GausiumAPIClient(http_client=http_client, token_manager=token)), http_client


def _response(data):
    return httpx.Response(200, json={"code": 0, "msg": "success", "traceId": "trace", "data": data})


async def test_status_enrichment_with_doc_example():
    async def handler(request):
        if request.url.path.endswith("oauth/token"):
            return httpx.Response(200, json={"access_token": "t", "expires_in": 9999999999999,
                                             "refresh_token": "r", "token_type": "bearer"})
        assert json.loads(request.content) == {"robotSnList": ["R1"]}
        return _response({"list": [{"robotSn": "R1", "batteryPercent": 90,
                                    "workState": 230}]})

    v3, client = _mock_v3(handler)
    try:
        result = await invoke("get_robot_status", {"robot_sn_list": ["R1"]}, v3)
        assert result["list"][0]["workState"] == 230
        assert result["list"][0]["work_state_name"] == "AUTO_TASKING"
        assert result["list"][0]["work_state_desc"] == "Auto task in progress"
        assert await invoke("describe_work_state", {"work_state": 100}, v3) == {
            "work_state": 100, "name": "IDLE", "description": "Idle", "is_terminal": True}
    finally:
        await client.aclose()


async def test_run_cleaning_task_happy_path():
    calls = []
    payloads = {
        "robot-capabilities/get": {"supportFusionTask": 1},
        "schedule-resources/list": {"robotSn": "R1", "maps": [{"mapId": "M1", "paths": [
            {"mapResourceId": "P1", "mapResourceType": "path", "mapResourceName": "Hall",
             "supportedActions": ["sweep"]}]}], "workModes": [{"mode": "sweep"}]},
        "persistence/create": {},
        "persistence/page": {"list": [{"fusionTaskId": "F1", "taskName": "Morning"}]},
        "commands/tasks/start": {"requestId": "Q1", "cmdStatus": 0},
        "commands/status/get": {"requestId": "Q1", "cmdStatus": 6, "cmdResultCode": ""},
    }

    async def handler(request):
        if request.url.path.endswith("oauth/token"):
            return httpx.Response(200, json={"access_token": "t", "expires_in": 9999999999999,
                                             "refresh_token": "r", "token_type": "bearer"})
        calls.append((request.url.path, json.loads(request.content)))
        return _response(next(value for key, value in payloads.items()
                              if request.url.path.endswith(key)))

    v3, client = _mock_v3(handler)
    try:
        result = await invoke("run_cleaning_task", {
            "robot_sn": "R1", "task_name": "Morning", "map_id": "M1",
            "resource_ids": ["P1"], "strength": "middle", "wait_seconds": 0,
        }, v3)
        assert result["final_status"] == 6
        assert result["list_task_definitions"]["list"][0]["fusionTaskId"] == "F1"
        assert calls[2][1]["mapResourceList"][0]["mapResourceId"] == "P1"
        assert calls[2][1]["workMode"] == {"mode": "sweep", "strength": "middle"}
        assert calls[3][1]["taskName"] == "Morning"
        assert calls[4][1]["fusionTaskId"] == "F1"
    finally:
        await client.aclose()
