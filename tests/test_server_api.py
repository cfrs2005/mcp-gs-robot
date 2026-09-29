"""HTTP integration tests using an in-process ASGI transport."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from gs_openapi.core.client import GausiumAPIClient
from gs_openapi.server import deps
from gs_openapi.server.app import create_app
from gs_openapi.server.routes.agent import PendingConfirms
from gs_openapi.server.static import mount_static
from gs_openapi.v3.api import GausiumV3


@pytest.fixture
def app():
    application = create_app()
    return application


@pytest.fixture
def client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def mock_v3(handler):
    class Token:
        async def get_valid_token(self):
            return "test"

        def invalidate(self):
            pass

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GausiumV3(GausiumAPIClient(http_client=http, token_manager=Token()))


def events(response):
    return [json.loads(line.removeprefix("data: ")) for line in response.text.splitlines()
            if line.startswith("data: ")]


@pytest.mark.asyncio
async def test_health_open_and_key_required(client, monkeypatch):
    monkeypatch.setenv("GS_SERVER_API_KEY", "secret")
    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["tools"] > 0
    denied = await client.post("/api/v1/tools/get_robot_status", json={"robot_sn_list": ["SN"]})
    assert denied.status_code == 401
    assert denied.json()["error"]["code"] == 401
    unknown = await client.post("/api/v1/tools/unknown", json={}, headers={"X-API-Key": "secret"})
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == 404


@pytest.mark.asyncio
async def test_tools_and_friendly_status(client, app, monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"code": 0, "data": {"list": [{
            "robotSn": "SN", "onlineStatus": "ONLINE", "batteryPercent": 78,
            "workState": 0, "currentMapName": "Main",
        }]}})

    app.dependency_overrides[deps.get_v3] = lambda: mock_v3(handler)
    result = await client.post("/api/v1/tools/get_robot_status", json={"robot_sn_list": ["SN"]})
    assert result.status_code == 200
    item = result.json()["result"]["list"][0]
    assert item["robotSn"] == "SN"
    assert "work_state_name" in item
    status = await client.get("/api/v1/robots/SN/status")
    assert status.status_code == 200
    assert status.json()["currentMapName"] == "Main"
    batch = await client.post("/api/v1/robots/status", json={"robot_sn_list": ["SN"]})
    assert isinstance(batch.json(), list)
    assert {"robotSn", "onlineStatus", "batteryPercent", "workState",
            "work_state_name", "currentMapName"} <= batch.json()[0].keys()
    assert all(body == {"robotSnList": ["SN"]} for body in seen)


@pytest.mark.asyncio
async def test_upstream_error_and_validation(client, app, monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    app.dependency_overrides[deps.get_v3] = lambda: mock_v3(
        lambda request: httpx.Response(200, json={
            "code": 123456, "msg": "upstream failed", "traceId": "trace-1", "data": None,
        })
    )
    response = await client.post("/api/v1/tools/get_robot_status", json={"robot_sn_list": ["SN"]})
    assert response.status_code == 502
    assert response.json() == {"error": {
        "code": 123456, "message": "upstream failed", "trace_id": "trace-1",
    }}
    invalid = await client.post("/api/v1/tools/get_robot_status", json={"robot_sn_list": []})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == 422


@pytest.mark.asyncio
async def test_robot_routes_map_registry_args(client, app, monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    calls = []

    async def invoke(name, args, v3):
        calls.append((name, args))
        return {"list": []} if name == "list_robots" else {"ok": True}

    monkeypatch.setattr("gs_openapi.server.routes.robots.registry.invoke", invoke)
    app.dependency_overrides[deps.get_v3] = lambda: object()
    requests = [
        ("GET", "/api/v1/robots?page=2&page_size=5", None, "list_robots"),
        ("GET", "/api/v1/robots/SN/maps/M/resources", None, "list_map_resources"),
        ("POST", "/api/v1/robots/SN/tasks/start", {"fusion_task_id": "T"}, "start_task"),
        ("POST", "/api/v1/robots/SN/navigation/pause", {}, "pause_navigation"),
        ("GET", "/api/v1/robots/SN/schedules/P?year=2026&month=9&day_of_month=1", None,
         "get_schedule"),
    ]
    for method, path, body, name in requests:
        response = await client.request(method, path, json=body)
        assert response.status_code == 200, response.text
        assert calls[-1][0] == name
    assert calls[1][1] == {"robot_sn": "SN", "map_id_list": ["M"]}
    assert calls[2][1] == {"robot_sn": "SN", "fusion_task_id": "T"}
    assert calls[4][1]["plan_uuid"] == "P"


@pytest.mark.asyncio
async def test_h5_list_robots_and_go_home_requires_map(client, app, monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)

    def handler(request):
        return httpx.Response(200, json={"list": [{"robotSn": "SN"}]})

    app.dependency_overrides[deps.get_v3] = lambda: mock_v3(handler)
    listed = await client.get("/api/v1/robots?page=1&page_size=100")
    assert listed.status_code == 200
    assert listed.json() == [{"robotSn": "SN"}]
    home = await client.post("/api/v1/robots/SN/navigation/go-home", json={})
    assert home.status_code == 422
    assert home.json()["error"]["code"] == 422


@pytest.mark.asyncio
async def test_h5_list_robots_maps_legacy_serial_number(client, app, monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)

    def handler(request):
        return httpx.Response(200, json={"robots": [{"serialNumber": "SN", "displayName": "d"}], "total": 1})

    app.dependency_overrides[deps.get_v3] = lambda: mock_v3(handler)
    listed = await client.get("/api/v1/robots")
    assert listed.json() == [{"serialNumber": "SN", "displayName": "d", "robotSn": "SN"}]


@pytest.mark.asyncio
async def test_create_agent_session_without_body(client, app, monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    from gs_openapi.agent.session import InMemorySessionStore

    app.dependency_overrides[deps.get_sessions] = lambda: InMemorySessionStore()
    created = await client.post("/api/v1/agent/sessions")
    assert created.status_code == 200
    assert created.json()["session_id"]


class FakeAgent:
    def __init__(self, gate):
        self.gate = gate

    async def run(self, session, text):
        session.messages.append({"role": "user", "content": text})
        if text == "danger":
            yield {"type": "confirm_required", "confirm_id": "c1", "name": "stop_task",
                   "input": {"robot_sn": "SN"}, "summary": "Stop SN"}
            approved = await self.gate.ask(session.session_id, "c1", "stop_task", {}, "Stop SN")
            yield {"type": "tool_result", "id": "t1", "name": "stop_task",
                   "output": {"approved": approved}, "is_error": not approved}
        else:
            yield {"type": "text_delta", "text": "hello"}
        session.messages.append({"role": "assistant", "content": "hello"})
        yield {"type": "done", "message_id": "m1", "usage": {}}


@pytest.mark.asyncio
async def test_agent_sse_and_confirm(client, app, monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    from gs_openapi.agent.session import InMemorySessionStore

    store = InMemorySessionStore()
    gate = PendingConfirms()
    app.dependency_overrides[deps.get_sessions] = lambda: store
    app.dependency_overrides[deps.get_agent] = lambda: FakeAgent(gate)
    app.dependency_overrides[deps.get_confirms] = lambda: gate
    created = await client.post("/api/v1/agent/sessions", json={})
    session_id = created.json()["session_id"]
    url = f"/api/v1/agent/sessions/{session_id}"
    text = await client.post(f"{url}/messages", json={"content": "hi"})
    assert text.headers["content-type"].startswith("text/event-stream")
    assert [event["type"] for event in events(text)] == ["text_delta", "done"]
    assert (await client.get(url)).json()["messages"][0] == {"role": "user", "content": "hi"}

    streaming = asyncio.create_task(client.post(f"{url}/messages", json={"content": "danger"}))
    for _ in range(100):
        if "c1" in gate.pending:
            break
        await asyncio.sleep(0.01)
    assert "c1" in gate.pending
    assert (await client.post(f"{url}/messages", json={"content": "busy"})).status_code == 409
    assert (await client.post(f"{url}/confirm", json={"confirm_id": "c1", "approve": True})).json() == {
        "ok": True,
    }
    response = await streaming
    assert [event["type"] for event in events(response)] == [
        "confirm_required", "tool_result", "done",
    ]
    assert events(response)[1]["output"] == {"approved": True}
    assert (await client.delete(url)).json() == {"ok": True}


@pytest.mark.asyncio
async def test_static_and_missing_static(client, app, tmp_path: Path, monkeypatch):
    monkeypatch.delenv("GS_SERVER_API_KEY", raising=False)
    index = await client.get("/")
    assert index.status_code == 200
    assert index.headers["content-type"].startswith("text/html")
    assert index.content == (Path(__file__).parents[1] /
                             "src/gs_openapi/server/static/index.html").read_bytes()
    assert (await client.get("/index.html")).content == index.content
    assert (await client.get("/robots/SN")).content == index.content
    assert (await client.get("/api/v1/this-does-not-exist")).status_code == 404
    assets_dir = Path(__file__).parents[1] / "src/gs_openapi/server/static/assets"
    assets = [(f.name, "text/css" if f.suffix == ".css" else "text/javascript")
              for f in sorted(assets_dir.iterdir()) if f.suffix in {".css", ".js"}]
    assert assets, "H5 build output missing: run `npm run build` in h5/"
    for filename, content_type in assets:
        asset = await client.get(f"/assets/{filename}")
        assert asset.status_code == 200
        assert asset.headers["content-type"].startswith(content_type)
        assert asset.content == (Path(__file__).parents[1] /
                                 "src/gs_openapi/server/static/assets" / filename).read_bytes()
    from fastapi import FastAPI

    missing = FastAPI()
    mount_static(missing, tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=missing),
                                 base_url="http://test") as fresh:
        assert (await fresh.get("/")).json() == {"message": "H5 not built", "docs": "/docs"}
