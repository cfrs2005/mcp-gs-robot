"""
Tests for gs_openapi.auth.token_manager — ms-epoch expiry handling, refresh
path, asyncio lock, and constructor injection. All HTTP via MockTransport.
"""

import asyncio
import time

import httpx
import pytest

from gs_openapi.auth.token_manager import (
    TokenManager,
    _compute_expires_at,
)
from gs_openapi.core.errors import GausiumAuthError


def _token_handler(token_payload):
    async def handler(request):
        import json

        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "token_type": "bearer",
                "access_token": token_payload["access_token"],
                "refresh_token": token_payload.get(
                    "refresh_token", "default-refresh"
                ),
                "expires_in": token_payload.get("expires_in", 1726111975164),
                "traceId": "trace-123",
            },
        )

    return handler


def test_compute_expires_at_ms_epoch():
    # 1726111975164 ms → 1726111975.164 s
    assert _compute_expires_at(1726111975164) == pytest.approx(1726111975.164)


def test_compute_expires_at_seconds_epoch():
    nowish = 2_000_000_000
    assert _compute_expires_at(nowish) == pytest.approx(float(nowish))


def test_compute_expires_at_duration():
    before = time.time()
    result = _compute_expires_at(3600)
    assert result == pytest.approx(before + 3600, abs=2)


async def test_get_new_token_ms_epoch_expiry():
    transport = httpx.MockTransport(
        _token_handler({"access_token": "tok-1", "expires_in": 1726111975164})
    )
    http_client = httpx.AsyncClient(transport=transport)
    try:
        tm = TokenManager(
            client_id="c",
            client_secret="s",
            open_access_key="k",
            http_client=http_client,
        )
        token = await tm.get_valid_token()
        assert token == "tok-1"
        # ms-epoch was divided by 1000, not treated as a duration.
        assert tm._expires_at == pytest.approx(1726111975164 / 1000.0)
        assert tm._refresh_token == "default-refresh"
    finally:
        await http_client.aclose()


async def test_refresh_path_uses_refresh_token():
    # First call acquires a token that expires almost immediately (duration),
    # second call (refresh) returns a fresh token with a far-future ms epoch.
    state = {"call": 0}

    async def handler(request):
        import json

        state["call"] += 1
        body = json.loads(request.content)
        if body.get("grant_type") == "refresh_token":
            return httpx.Response(
                200,
                json={
                    "access_token": "refreshed-tok",
                    "refresh_token": "refreshed-rt",
                    "expires_in": 9999999999999,
                    "token_type": "bearer",
                },
            )
        # Initial acquisition: short duration so it is "expired" after sleep.
        return httpx.Response(
            200,
            json={
                "access_token": "initial-tok",
                "refresh_token": "initial-rt",
                "expires_in": 1,
                "token_type": "bearer",
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    try:
        tm = TokenManager(
            client_id="c",
            client_secret="s",
            open_access_key="k",
            http_client=http_client,
            # No buffer so a 1s expiry is immediately invalid.
        )
        tm._refresh_buffer = 0
        first = await tm.get_valid_token()
        assert first == "initial-tok"
        # Force expiry.
        tm._expires_at = time.time() - 1
        second = await tm.get_valid_token()
        assert second == "refreshed-tok"
        assert tm._refresh_token == "refreshed-rt"
        assert state["call"] == 2
    finally:
        await http_client.aclose()


async def test_invalidate_forces_reacquisition():
    state = {"call": 0}

    async def handler(request):
        import json

        state["call"] += 1
        return httpx.Response(
            200,
            json={
                "access_token": f"tok-{state['call']}",
                "refresh_token": "rt",
                "expires_in": 9999999999999,
                "token_type": "bearer",
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    try:
        tm = TokenManager(
            client_id="c", client_secret="s", open_access_key="k",
            http_client=http_client,
        )
        assert await tm.get_valid_token() == "tok-1"
        tm.invalidate()
        assert await tm.get_valid_token() == "tok-2"
        assert state["call"] == 2
    finally:
        await http_client.aclose()


def test_missing_credentials_raises_auth_error(monkeypatch):
    # conftest sets dummy GS_* env vars; clear them so the fallback fails.
    for var in ("GS_CLIENT_ID", "GS_CLIENT_SECRET", "GS_OPEN_ACCESS_KEY"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(GausiumAuthError):
        TokenManager(client_id=None, client_secret=None, open_access_key=None)


async def test_concurrent_callers_serialised_by_lock():
    # A single token acquisition should happen once even with many concurrent
    # callers (the lock serialises the refresh/acquire path).
    state = {"call": 0}

    async def handler(request):
        import asyncio
        import json

        state["call"] += 1
        await asyncio.sleep(0.01)
        return httpx.Response(
            200,
            json={
                "access_token": "single-tok",
                "refresh_token": "rt",
                "expires_in": 9999999999999,
                "token_type": "bearer",
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    try:
        tm = TokenManager(
            client_id="c", client_secret="s", open_access_key="k",
            http_client=http_client,
        )
        results = await asyncio.gather(*(tm.get_valid_token() for _ in range(8)))
        assert all(r == "single-tok" for r in results)
        # Only one HTTP acquisition should have occurred.
        assert state["call"] == 1
    finally:
        await http_client.aclose()
