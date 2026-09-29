"""
Shared pytest configuration for the gs_openapi test suite.

Sets dummy GS_* credentials so that TokenManager can be constructed without
real secrets. No network access is performed by any test; all HTTP traffic is
served by :class:`httpx.MockTransport`.
"""

import os

# Dummy credentials — must be set before any gs_openapi import that reads
# the environment (e.g. config.py reads GS_BASE_URL at import time).
os.environ.setdefault("GS_CLIENT_ID", "test-client-id")
os.environ.setdefault("GS_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("GS_OPEN_ACCESS_KEY", "test-open-access-key")
os.environ.setdefault("GS_BASE_URL", "https://openapi.gs-robot.com/")

import pytest


@pytest.fixture
def dummy_credentials():
    return {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "open_access_key": "test-open-access-key",
    }
