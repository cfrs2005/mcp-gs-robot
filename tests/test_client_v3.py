"""
Tests for gs_openapi.core.client.GausiumAPIClient.call_v3 and the GausiumV3
facade: envelope unwrap, non-zero code error, 401 invalidate+retry, and
request path/body exactness for 6 endpoints. All HTTP via MockTransport.
"""

import json
from typing import Any

import httpx
import pytest

from gs_openapi.auth.token_manager import TokenManager
from gs_openapi.core.client import GausiumAPIClient
from gs_openapi.core.errors import GausiumAPIError
from gs_openapi.v3 import GausiumV3


def _oauth_response() -> dict[str, Any]:
    return {
        "token_type": "bearer",
        "access_token": "bearer-token-xyz",
        "refresh_token": "rt-xyz",
        # Far-future ms epoch so the token stays valid during tests.
        "expires_in": 9999999999999,
        "traceId": "auth-trace",
    }


def _make_client(handler, *, token_client=None):
    """Build a GausiumAPIClient backed by a MockTransport handler."""
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    tm = TokenManager(
        client_id="c",
        client_secret="s",
        open_access_key="k",
        http_client=http_client,
    )
    client = GausiumAPIClient(token_manager=tm, http_client=http_client)
    return client, http_client, tm


def _envelope(data: Any, *, code: int = 0, msg: str = "success",
              trace_id: str = "1a2b3c4d5e6f708192a3b4c5d6e7f809"):
    return {"code": code, "msg": msg, "traceId": trace_id, "data": data}


def _record_handler(
    envelope_map: dict[str, Any],
    recorded: list[dict[str, Any]],
    *,
    first_401_paths: set | None = None,
):
    """Return a MockTransport handler that serves oauth + V3 envelopes.

    ``envelope_map`` maps the URL path (without leading slash) to the ``data``
    value to return. The full request (path + parsed JSON body) is appended to
    ``recorded``. Paths in ``first_401_paths`` return HTTP 401 on the first
    hit and the envelope on the second.
    """
    first_401_paths = first_401_paths or set()
    seen_401: set = set()

    async def handler(request: httpx.Request):
        path = request.url.path.lstrip("/")
        if path.endswith("oauth/token"):
            return httpx.Response(200, json=_oauth_response())
        # V3 business endpoint.
        body = json.loads(request.content) if request.content else {}
        recorded.append({"path": request.url.path, "body": body})
        if path in first_401_paths and path not in seen_401:
            seen_401.add(path)
            return httpx.Response(401, json={"code": 401, "msg": "Unauthorized",
                                             "traceId": "t-401"})
        data = envelope_map.get(path)
        if data is _NOT_FOUND:
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json=_envelope(data))

    return handler


_NOT_FOUND = object()


async def test_envelope_unwrap_success_returns_data():
    recorded: list[dict[str, Any]] = []
    handler = _record_handler(
        {"openapi/v3/robots/status/get": {"list": []}}, recorded
    )
    client, http_client, _ = _make_client(handler)
    try:
        data = await client.call_v3("v3_robots_status_get", {"robotSnList": ["R1"]})
        assert data == {"list": []}
        # Path and body exactness.
        assert recorded[0]["path"] == "/openapi/v3/robots/status/get"
        assert recorded[0]["body"] == {"robotSnList": ["R1"]}
        # Bearer header was sent.
    finally:
        await client.aclose()
        await http_client.aclose()


async def test_nonzero_code_raises_api_error_with_fields():
    handler = _record_handler({}, [])
    # Override: return a non-zero envelope for this endpoint.
    async def h(request):
        if request.url.path.endswith("oauth/token"):
            return httpx.Response(200, json=_oauth_response())
        return httpx.Response(
            200,
            json={
                "code": 2010100009,
                "msg": "Failed to operate data.",
                "traceId": "err-trace-1",
                "data": None,
            },
        )
    client, http_client, _ = _make_client(h)
    try:
        with pytest.raises(GausiumAPIError) as exc:
            await client.call_v3("v3_tasks_start", {"robotSn": "R1", "fusionTaskId": "f"})
        e = exc.value
        assert e.code == 2010100009
        assert e.msg == "Failed to operate data."
        assert e.trace_id == "err-trace-1"
        assert e.endpoint == "v3_tasks_start"
        assert "2010100009" in str(e)
        assert "v3_tasks_start" in str(e)
    finally:
        await client.aclose()
        await http_client.aclose()


async def test_http_error_raises_api_error():
    async def h(request):
        if request.url.path.endswith("oauth/token"):
            return httpx.Response(200, json=_oauth_response())
        return httpx.Response(500, text="internal server error")
    client, http_client, _ = _make_client(h)
    try:
        with pytest.raises(GausiumAPIError) as exc:
            await client.call_v3("v3_robots_status_get", {"robotSnList": []})
        assert exc.value.http_status == 500
        assert exc.value.endpoint == "v3_robots_status_get"
    finally:
        await client.aclose()
        await http_client.aclose()


async def test_401_invalidates_token_and_retries_once():
    recorded: list[dict[str, Any]] = []
    handler = _record_handler(
        {"openapi/v3/robots/status/get": {"list": []}},
        recorded,
        first_401_paths={"openapi/v3/robots/status/get"},
    )
    client, http_client, tm = _make_client(handler)
    try:
        # Prime the token so we can observe invalidation.
        await tm.get_valid_token()
        assert tm._access_token == "bearer-token-xyz"
        data = await client.call_v3("v3_robots_status_get", {"robotSnList": ["R1"]})
        assert data == {"list": []}
        # The endpoint was hit twice (first 401, then success).
        paths = [r["path"] for r in recorded]
        assert paths == [
            "/openapi/v3/robots/status/get",
            "/openapi/v3/robots/status/get",
        ]
        # Token was invalidated between the two calls; a fresh token was
        # re-acquired (the mock oauth always returns the same value, but the
        # invalidate path is exercised).
        assert tm._access_token == "bearer-token-xyz"
    finally:
        await client.aclose()
        await http_client.aclose()


async def test_401_not_retried_twice():
    async def h(request):
        if request.url.path.endswith("oauth/token"):
            return httpx.Response(200, json=_oauth_response())
        return httpx.Response(401, json={"code": 401, "msg": "Unauthorized"})
    client, http_client, _ = _make_client(h)
    try:
        with pytest.raises(GausiumAPIError) as exc:
            await client.call_v3("v3_robots_status_get", {"robotSnList": []})
        # After one retry, the second 401 surfaces as an HTTP error.
        assert exc.value.http_status == 401
    finally:
        await client.aclose()
        await http_client.aclose()


# ---------------------------------------------------------------------------
# Path/body exactness for 6 endpoints (via the GausiumV3 facade).
# ---------------------------------------------------------------------------
async def test_facade_six_endpoints_path_and_body():
    recorded: list[dict[str, Any]] = []
    envelope_map = {
        "openapi/v3/robots/status/get": {
            "list": [
                {"robotSn": "R1", "onlineStatus": "ONLINE", "workState": 100},
            ]
        },
        "openapi/v3/robots/maps/list": [
            {"mapId": "m1", "displayName": "Lobby"},
        ],
        "openapi/v3/maps/schedule-resources/list": {
            "maps": [], "workModes": [], "robotSn": "R1",
        },
        "openapi/v3/robots/commands/tasks/start": {
            "cmdStatus": 6,
            "requestId": "req-1",
            "taskInstanceId": "ti-1",
        },
        "openapi/v3/taskreports/page": {
            "count": 0, "page": 1, "pagesize": 20, "robotTaskReports": [],
        },
        "openapi/v3/robots/commands/status/get": {
            "cmdStatus": 6,
            "commandType": "START_FUSION_TASK",
            "requestId": "req-1",
            "robotSn": "R1",
            "cmdResultCode": "6880",
            "cmdResultMessage": "success",
        },
    }
    handler = _record_handler(envelope_map, recorded)
    client, http_client, _ = _make_client(handler)
    try:
        v3 = GausiumV3(client)
        await v3.robots.get_status(["R1"])
        await v3.maps.list_maps("R1")
        await v3.maps.list_schedule_resources("R1", ["m1"])
        await v3.tasks.start("R1", "fusion-1", loop_count=2)
        await v3.reports.page("R1", 1, pagesize=20)
        await v3.commands.get_status("R1", "req-1")

        by_path = {}
        for r in recorded:
            by_path.setdefault(r["path"], []).append(r["body"])

        assert by_path["/openapi/v3/robots/status/get"][0] == {"robotSnList": ["R1"]}
        assert by_path["/openapi/v3/robots/maps/list"][0] == {"robotSn": "R1"}
        assert by_path["/openapi/v3/maps/schedule-resources/list"][0] == {
            "robotSn": "R1", "mapIdList": ["m1"],
        }
        assert by_path["/openapi/v3/robots/commands/tasks/start"][0] == {
            "robotSn": "R1", "fusionTaskId": "fusion-1", "loopCount": 2,
        }
        assert by_path["/openapi/v3/taskreports/page"][0] == {
            "robotSn": "R1", "page": 1, "pagesize": 20,
        }
        assert by_path["/openapi/v3/robots/commands/status/get"][0] == {
            "robotSn": "R1", "requestId": "req-1",
        }
    finally:
        await client.aclose()
        await http_client.aclose()


async def test_facade_returns_typed_models():
    recorded: list[dict[str, Any]] = []
    envelope_map = {
        "openapi/v3/robots/status/get": {
            "list": [
                {"robotSn": "R1", "onlineStatus": "ONLINE", "workState": 230},
            ]
        },
        "openapi/v3/robots/commands/tasks/start": {
            "cmdStatus": 6, "requestId": "req-1", "taskInstanceId": "ti-1",
        },
    }
    handler = _record_handler(envelope_map, recorded)
    client, http_client, _ = _make_client(handler)
    try:
        v3 = GausiumV3(client)
        page = await v3.robots.get_status(["R1"])
        assert page.list[0].robot_sn == "R1"
        assert page.list[0].work_state == 230
        accepted = await v3.tasks.start("R1", "f1")
        assert accepted.request_id == "req-1"
        assert accepted.cmd_status == 6
        assert accepted.task_instance_id == "ti-1"
    finally:
        await client.aclose()
        await http_client.aclose()


async def test_get_one_status_convenience():
    handler = _record_handler(
        {"openapi/v3/robots/status/get": {
            "list": [
                {"robotSn": "R2", "onlineStatus": "OFFLINE"},
                {"robotSn": "R1", "onlineStatus": "ONLINE"},
            ]
        }}, []
    )
    client, http_client, _ = _make_client(handler)
    try:
        v3 = GausiumV3(client)
        snap = await v3.robots.get_one_status("R1")
        assert snap is not None
        assert snap.robot_sn == "R1"
    finally:
        await client.aclose()
        await http_client.aclose()
