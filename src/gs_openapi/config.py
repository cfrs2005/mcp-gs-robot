"""
Configuration module for Gausium OpenAPI.

This module contains all constants and environment variable configurations
used throughout the application. Legacy constants are preserved for backward
compatibility; V3 additions add environment overrides for the base URL and
HTTP timeout.
"""

import os

# Base URL for Gausium OpenAPI (ensure trailing slash for urljoin).
# Allow override via the GS_BASE_URL environment variable (V3).
GAUSIUM_BASE_URL = os.getenv("GS_BASE_URL", "https://openapi.gs-robot.com/")
if not GAUSIUM_BASE_URL.endswith("/"):
    GAUSIUM_BASE_URL = GAUSIUM_BASE_URL + "/"

# Default HTTP timeout in seconds for OpenAPI calls (V3).
GS_HTTP_TIMEOUT = float(os.getenv("GS_HTTP_TIMEOUT", "30"))

# API Paths
TOKEN_PATH = "gas/api/v1alpha1/oauth/token"  # Relative path (kept for legacy + V3 auth)
ROBOTS_PATH = "v1alpha1/robots"              # Relative path
MAP_LIST_PATH = "openapi/v1/map/robotMap/list"  # Path for listing maps (V1)

# Environment Variables
ENV_VAR_CLIENT_ID = "GS_CLIENT_ID"
ENV_VAR_CLIENT_SECRET = "GS_CLIENT_SECRET"
ENV_VAR_OPEN_ACCESS_KEY = "GS_OPEN_ACCESS_KEY"
ENV_VAR_BASE_URL = "GS_BASE_URL"
ENV_VAR_HTTP_TIMEOUT = "GS_HTTP_TIMEOUT"

# API Authentication - 所有机密信息必须通过环境变量设置，绝不硬编码
