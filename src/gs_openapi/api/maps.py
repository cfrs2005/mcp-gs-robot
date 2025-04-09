"""
Map API module for Gausium OpenAPI.

This module provides functions for interacting with the Gausium Map Service API.
"""

from typing import Any, Dict, List
import httpx
from urllib.parse import urljoin

from ..config import GAUSIUM_BASE_URL, MAP_LIST_PATH
from ..auth.token_manager import TokenManager

async def list_robot_maps(token_manager: TokenManager, robot_sn: str) -> List[Dict[str, Any]]:
    """Fetches the list of maps associated with a specific robot.

    Args:
        token_manager: TokenManager instance for authentication.
        robot_sn: The serial number of the target robot.

    Returns:
        A list of dictionaries, each containing map ID and map name.

    Raises:
        ValueError: If robot_sn is empty.
        httpx.HTTPStatusError: If the API call returns an unsuccessful status code.
        httpx.RequestError: If there is an issue connecting to the API.
        KeyError: If the response format is unexpected (missing 'data' key).
    """
    if not robot_sn:
        raise ValueError("Robot serial number (robotSn) cannot be empty")

    try:
        access_token = await token_manager.get_valid_token()
        full_map_list_url = urljoin(GAUSIUM_BASE_URL, MAP_LIST_PATH)

        # Prepare request body as per curl example
        request_body = {"robotSn": robot_sn}

        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json' # Ensure content type is set for POST
            }
            response = await client.post(
                full_map_list_url,
                headers=headers,
                json=request_body # Send data as JSON body
            )
            response.raise_for_status()
            response_data = response.json()

            # Check for successful API response code within JSON
            if response_data.get("code") != 0:
                raise httpx.HTTPStatusError(
                    f"API returned error code {response_data.get('code')}: {response_data.get('msg')}", 
                    request=response.request, 
                    response=response
                )

            # Extract the map list from the 'data' field
            map_list = response_data.get("data", [])
            if not isinstance(map_list, list):
                 raise KeyError("API response format error: 'data' key is not a list or is missing.")
            
            return map_list

    except httpx.HTTPStatusError as e:
        # Log the error already raised or the one we raised based on 'code'
        print(f"Error listing maps for robot {robot_sn}: {str(e)}")
        raise
    except httpx.RequestError as e:
        print(f"Network error listing maps for robot {robot_sn}: {e}")
        raise
    except KeyError as e:
         print(f"API response format error for robot {robot_sn}: {str(e)}")
         raise # Re-raise the KeyError
