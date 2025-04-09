"""
Gausium MCP implementation module.

This module provides the main MCP implementation for the Gausium OpenAPI.
"""

from typing import Any, Dict, Optional, List
from mcp.server.fastmcp import FastMCP

from ..auth.token_manager import TokenManager
from ..api.robots import list_robots, get_robot_status, list_robot_task_reports
from ..api.maps import list_robot_maps

class GausiumMCP(FastMCP):
    """Extended FastMCP with Gausium API support."""
    
    def __init__(self, name: str):
        """Initialize GausiumMCP with TokenManager.
        
        Args:
            name: The name of the MCP instance
        """
        super().__init__(name)
        self.token_manager = TokenManager()

    async def list_robots(
        self,
        page: int = 1,
        page_size: int = 10,
        relation: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches the list of robots from the Gausium OpenAPI.

        Args:
            page: The page number to retrieve (must be > 0)
            page_size: The number of items per page
            relation: Optional relation type (e.g., 'contract'). If None, uses API default

        Returns:
            A dictionary containing the robot list data from the API

        Raises:
            httpx.HTTPStatusError: If an API call returns an unsuccessful status code
            httpx.RequestError: If there is an issue connecting to the API
        """
        return await list_robots(
            token_manager=self.token_manager,
            page=page,
            page_size=page_size,
            relation=relation
        )

    async def get_robot_status(self, serial_number: str) -> Dict[str, Any]:
        """Fetches the status of a specific robot.

        Args:
            serial_number: The serial number of the target robot.

        Returns:
            A dictionary containing the robot status data.

        Raises:
            ValueError: If serial_number is empty.
            httpx.HTTPStatusError: If an API call returns an unsuccessful status code.
            httpx.RequestError: If there is an issue connecting to the API.
        """
        return await get_robot_status(
            token_manager=self.token_manager,
            serial_number=serial_number
        )

    async def list_robot_task_reports(
        self,
        serial_number: str,
        page: int = 1,
        page_size: int = 100,
        start_time_utc_floor: Optional[str] = None,
        start_time_utc_upper: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches the task reports for a specific robot.

        Args:
            serial_number: The serial number of the target robot.
            page: The page number to retrieve (must be > 0).
            page_size: The number of items per page.
            start_time_utc_floor: Optional start time filter (ISO 8601 format string).
            start_time_utc_upper: Optional end time filter (ISO 8601 format string).

        Returns:
            A dictionary containing the robot task reports data.

        Raises:
            ValueError: If serial_number is empty.
            httpx.HTTPStatusError: If an API call returns an unsuccessful status code.
            httpx.RequestError: If there is an issue connecting to the API.
        """
        return await list_robot_task_reports(
            token_manager=self.token_manager,
            serial_number=serial_number,
            page=page,
            page_size=page_size,
            start_time_utc_floor=start_time_utc_floor,
            start_time_utc_upper=start_time_utc_upper
        )

    async def list_robot_maps(self, robot_sn: str) -> List[Dict[str, Any]]:
        """Fetches the list of maps associated with a specific robot.

        Args:
            robot_sn: The serial number of the target robot.

        Returns:
            A list of dictionaries, each containing map ID and map name.

        Raises:
            ValueError: If robot_sn is empty.
            httpx.HTTPStatusError: If the API call returns an unsuccessful status code.
            httpx.RequestError: If there is an issue connecting to the API.
            KeyError: If the response format is unexpected.
        """
        return await list_robot_maps(
            token_manager=self.token_manager,
            robot_sn=robot_sn
        )
