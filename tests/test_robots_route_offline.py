"""Offline robots must not break the H5 robot status routes (upstream 230003)."""

import json

import httpx
import pytest

from gs_openapi.core.client import GausiumAPIClient
from gs_openapi.server import deps
from gs_openapi.server.app import create_app
from gs_openapi.server.routes import robots
from gs_openapi.v3.api import GausiumV3

OFFLINE = {"OFF-1", "OFF-2"}


def mock_v3(handler):
    class Token:
        async def get_valid_token(self):
            return "test"

        def invalidate(self):
            pass

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GausiumV3(GausiumAPIClient(http_client=http, token_manager=Token()))


def upstream(seen):
    """Mimic the V3 snapshot endpoint: any offline SN in the batch fails the whole call."""

    def handler(request):
        sns = json.loads(request.content)["robotSnList"]
        seen.append(sns)
        if OFFLINE & set(sns):
            return httpx.Response(200, json={
                "code": 230003, "msg": "Robot columbus routing failed.", "traceId": "trace-x",
            })
        return httpx.Response(200, json={"code": 0, "data": {"list": [
            {"robotSn": sn, "onlineStatus": "ONLINE", "batteryPercent": 50, "workState": 0}
            for sn in sns
        ]}})

    return handler


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    monkeypatch.setattr(robots, "FALLBACK_INTERVAL_SECONDS", 0)
    app = create_app()
    seen: list[list[str]] = []
    app.dependency_overrides[deps.get_v3] = lambda: mock_v3(upstream(seen))
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    return client, seen


@pytest.mark.asyncio
async def test_all_online_batch_is_single_call(setup):
    client, seen = setup
    response = await client.post("/api/v1/robots/status", json={"robot_sn_list": ["ON-1", "ON-2"]})
    assert response.status_code == 200
    assert [item["robotSn"] for item in response.json()] == ["ON-1", "ON-2"]
    assert all("reachable" not in item for item in response.json())
    assert seen == [["ON-1", "ON-2"]]


@pytest.mark.asyncio
async def test_batch_with_offline_degrades_only_offline(setup):
    client, seen = setup
    sns = ["ON-1", "OFF-1", "ON-2", "OFF-2"]
    response = await client.post("/api/v1/robots/status", json={"robot_sn_list": sns})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert [item["robotSn"] for item in body] == sns  # order preserved
    by_sn = {item["robotSn"]: item for item in body}
    for sn in ("ON-1", "ON-2"):
        assert by_sn[sn]["onlineStatus"] == "ONLINE"
        assert by_sn[sn]["work_state_name"] is not None
    for sn in OFFLINE:
        assert by_sn[sn]["onlineStatus"] == "OFFLINE"
        assert by_sn[sn]["reachable"] is False
        assert by_sn[sn]["error"] == {
            "code": 230003, "message": "Robot is offline or not connected to the cloud",
            "trace_id": "trace-x",
        }
    assert "columbus" not in response.text
    # One failed batch call, then exactly one paced call per robot.
    assert seen == [sns] + [[sn] for sn in sns]


@pytest.mark.asyncio
async def test_single_offline_status_is_200_placeholder(setup):
    client, seen = setup
    response = await client.get("/api/v1/robots/OFF-1/status")
    assert response.status_code == 200
    assert response.json()["reachable"] is False
    assert response.json()["onlineStatus"] == "OFFLINE"
    # Clients localize by the structured code; the text is English and carries no CJK.
    error = response.json()["error"]
    assert error["code"] == 230003
    assert error["message"].isascii()
    assert seen == [["OFF-1"]]
    online = await client.get("/api/v1/robots/ON-1/status")
    assert online.status_code == 200 and online.json()["onlineStatus"] == "ONLINE"


@pytest.mark.asyncio
async def test_other_upstream_errors_still_surface(monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    app = create_app()
    app.dependency_overrides[deps.get_v3] = lambda: mock_v3(lambda request: httpx.Response(
        200, json={"code": 110003, "msg": "Robot is not bound to the current user.", "traceId": "t"},
    ))
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    response = await client.post("/api/v1/robots/status", json={"robot_sn_list": ["A", "B"]})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == 110003


@pytest.mark.asyncio
async def test_batch_input_validation(setup):
    client, seen = setup
    empty = await client.post("/api/v1/robots/status", json={"robot_sn_list": []})
    assert empty.status_code == 422
    too_many = await client.post(
        "/api/v1/robots/status", json={"robot_sn_list": [f"SN-{i}" for i in range(101)]},
    )
    assert too_many.status_code == 422
    assert seen == []
