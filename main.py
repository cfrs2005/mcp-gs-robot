"""
Main entry point for the Gausium OpenAPI application.

This module initializes and runs the MCP server with Gausium API support.
"""
import logging
import sys
from typing import Optional

from src.gs_openapi.mcp.gausium_mcp import GausiumMCP

# --- Logging Configuration (Simplified) ---
# Keep it simple for now to ensure basic functionality
LOG_FORMAT = "%(asctime)s.%(msecs)03d - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configure root logger ONLY
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
# --- End Logging Configuration ---

# Create MCP instance
mcp = GausiumMCP("gs-openapi")

# Define list_robots tool
@mcp.tool()
async def list_robots(page: int = 1, page_size: int = 10, relation: str = None):
    """Fetches the list of robots from the Gausium OpenAPI.
    
    Based on: https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/List%20Robots

    Args:
        page: The page number to retrieve (must be > 0).
        page_size: The number of items per page.
        relation: Optional relation type (e.g., 'contract').

    Returns:
        A dictionary containing the robot list data from the API.
    """
    return await mcp.list_robots(page=page, page_size=page_size, relation=relation)

# Define get_robot_status tool
@mcp.tool()
async def get_robot_status(serial_number: str):
    """Fetches the status of a specific robot by its serial number.
    
    Based on: https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/V1%20Get%20Robot%20Status

    Args:
        serial_number: The serial number of the target robot (e.g., 'TEST00-0000-000-S003').

    Returns:
        A dictionary containing the detailed status of the robot.
    """
    return await mcp.get_robot_status(serial_number=serial_number)

# Define list_robot_task_reports tool
@mcp.tool(name="list_robot_task_reports")
async def list_robot_task_reports_tool(
    serial_number: str,
    page: int = 1,
    page_size: int = 100,
    start_time_utc_floor: Optional[str] = None,
    start_time_utc_upper: Optional[str] = None
):
    """Fetches the task reports for a specific robot.
    
    Allows filtering by time range (optional).
    Based on: https://developer.gs-robot.com/zh_CN/Robot%20Cleaning%20Data%20Service/V1%20List%20Robot%20Task%20Reports

    Args:
        serial_number: The serial number of the target robot.
        page: The page number to retrieve (default: 1).
        page_size: The number of items per page (default: 100).
        start_time_utc_floor: Optional start time filter (ISO 8601 format string, e.g., '2024-09-11T00:00:00Z').
        start_time_utc_upper: Optional end time filter (ISO 8601 format string, e.g., '2024-09-12T00:00:00Z').

    Returns:
        A dictionary containing the robot task reports data.
    """
    return await mcp.list_robot_task_reports(
        serial_number=serial_number,
        page=page,
        page_size=page_size,
        start_time_utc_floor=start_time_utc_floor,
        start_time_utc_upper=start_time_utc_upper
    )

# Define list_robot_maps tool
@mcp.tool()
async def list_robot_maps(robot_sn: str):
    """Fetches the list of maps associated with a specific robot.

    Based on: https://developer.gs-robot.com/zh_CN/Robot%20Map%20Service/V1%20List%20Robot%20Map
    Note: This API uses POST method with robotSn in the JSON body.

    Args:
        robot_sn: The serial number of the target robot (e.g., 'GS008-0180-C7P-0000').

    Returns:
        A list of dictionaries, each containing 'mapId' and 'mapName'.
    """
    return await mcp.list_robot_maps(robot_sn=robot_sn)

if __name__ == "__main__":
    logging.info("Starting Gausium MCP server using mcp.run() with simplified logging...")
    # Run using mcp.run()
    mcp.run(transport='sse')
    # mcp.run(transport='stdio')

