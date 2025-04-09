"""
Configuration module for Gausium OpenAPI.

This module contains all constants and environment variable configurations
used throughout the application.
"""

import os
from urllib.parse import urljoin # Import urljoin

# Base URL for Gausium OpenAPI (ensure trailing slash for urljoin)
GAUSIUM_BASE_URL = "https://openapi.gs-robot.com/" 

# API Paths
TOKEN_PATH = "gas/api/v1alpha1/oauth/token" # Relative path
ROBOTS_PATH = "v1alpha1/robots"             # Relative path
MAP_LIST_PATH = "openapi/v1/map/robotMap/list" # Path for listing maps

# Environment Variables
ENV_VAR_CLIENT_ID = "GS_CLIENT_ID"
ENV_VAR_CLIENT_SECRET = "GS_CLIENT_SECRET"
ENV_VAR_OPEN_ACCESS_KEY = "GS_OPEN_ACCESS_KEY"

