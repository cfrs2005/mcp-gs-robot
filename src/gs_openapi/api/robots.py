"""
Robot API module for Gausium OpenAPI.

This module provides functions for interacting with the Gausium Robots API.
"""

from typing import Any, Dict, Optional
import httpx
from urllib.parse import urljoin

from ..config import GAUSIUM_BASE_URL, ROBOTS_PATH
from ..auth.token_manager import TokenManager

async def list_robots(
    token_manager: TokenManager,
    page: int = 1,
    page_size: int = 10,
    relation: Optional[str] = None
) -> Dict[str, Any]:
    """Fetches the list of robots from the Gausium OpenAPI.

    Args:
        token_manager: TokenManager instance for authentication
        page: The page number to retrieve (must be > 0)
        page_size: The number of items per page
        relation: Optional relation type (e.g., 'contract'). If None, uses API default

    Returns:
        A dictionary containing the robot list data from the API

    Raises:
        httpx.HTTPStatusError: If an API call returns an unsuccessful status code
        httpx.RequestError: If there is an issue connecting to the API
    """
    try:
        # Get a valid token from the manager
        access_token = await token_manager.get_valid_token()
        
        # Construct full URL using urljoin
        full_robots_url = urljoin(GAUSIUM_BASE_URL, ROBOTS_PATH)
        
        # List Robots using the obtained token
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {access_token}'}
            # Create query parameters dictionary
            query_params = {
                "page": page,
                "pageSize": page_size,
            }
            if relation is not None:
                query_params["relation"] = relation

            robots_response = await client.get(
                full_robots_url,
                headers=headers,
                params=query_params
            )
            robots_response.raise_for_status()
            return robots_response.json()

    except httpx.HTTPStatusError as e:
        print(f"Error listing robots: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        print(f"Network error listing robots: {e}")
        raise

async def get_robot_status(token_manager: TokenManager, serial_number: str) -> Dict[str, Any]:
    """Fetches the status of a specific robot from the Gausium OpenAPI.

    Args:
        token_manager: TokenManager instance for authentication.
        serial_number: The serial number of the target robot.

    Returns:
        A dictionary containing the robot status data from the API.

    Raises:
        ValueError: If serial_number is empty.
        httpx.HTTPStatusError: If the API call returns an unsuccessful status code.
        httpx.RequestError: If there is an issue connecting to the API.
    """
    if not serial_number:
        raise ValueError("Serial number cannot be empty")

    try:
        # Get a valid token from the manager
        access_token = await token_manager.get_valid_token()

        # Construct the specific path for the robot status
        # Path format: v1alpha1/robots/{serial_number}/status
        status_path = f"{ROBOTS_PATH}/{serial_number}/status"
        
        # Construct full URL using urljoin
        full_status_url = urljoin(GAUSIUM_BASE_URL, status_path)
        
        # Get Robot Status using the obtained token
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {access_token}'}

            status_response = await client.get(
                full_status_url,
                headers=headers
            )
            status_response.raise_for_status()
            return status_response.json()

    except httpx.HTTPStatusError as e:
        print(f"Error getting status for robot {serial_number}: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        print(f"Network error getting status for robot {serial_number}: {e}")
        raise

async def list_robot_task_reports(
    token_manager: TokenManager,
    serial_number: str,
    page: int = 1,
    page_size: int = 100, # Default page size from curl example
    start_time_utc_floor: Optional[str] = None,
    start_time_utc_upper: Optional[str] = None
) -> Dict[str, Any]:
    """Fetches the task reports for a specific robot.

    Args:
        token_manager: TokenManager instance for authentication.
        serial_number: The serial number of the target robot.
        page: The page number to retrieve (must be > 0).
        page_size: The number of items per page.
        start_time_utc_floor: Optional start time filter (ISO 8601 format string, e.g., '2024-09-11T00:00:00Z').
        start_time_utc_upper: Optional end time filter (ISO 8601 format string, e.g., '2024-09-12T00:00:00Z').

    Returns:
        A dictionary containing the robot task reports data.

    Raises:
        ValueError: If serial_number is empty.
        httpx.HTTPStatusError: If the API call returns an unsuccessful status code.
        httpx.RequestError: If there is an issue connecting to the API.
    """
    if not serial_number:
        raise ValueError("Serial number cannot be empty")

    try:
        access_token = await token_manager.get_valid_token()

        # Construct the specific path: v1alpha1/robots/{serial_number}/taskReports
        reports_path = f"{ROBOTS_PATH}/{serial_number}/taskReports"
        full_reports_url = urljoin(GAUSIUM_BASE_URL, reports_path)

        # Prepare query parameters, including optionals only if provided
        query_params = {
            "page": page,
            "pageSize": page_size,
        }
        if start_time_utc_floor:
            query_params["startTimeUtcFloor"] = start_time_utc_floor
        if start_time_utc_upper:
            query_params["startTimeUtcUpper"] = start_time_utc_upper

        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {access_token}'}
            reports_response = await client.get(
                full_reports_url,
                headers=headers,
                params=query_params # Pass constructed query parameters
            )
            reports_response.raise_for_status()
            return reports_response.json()

    except httpx.HTTPStatusError as e:
        print(f"Error listing task reports for robot {serial_number}: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        print(f"Network error listing task reports for robot {serial_number}: {e}")
        raise
