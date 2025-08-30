"""
Main entry point for the Gausium OpenAPI application.

This module initializes and runs the MCP server with Gausium API support.
"""
import logging
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .mcp.gausium_mcp import GausiumMCP
from .utils.robot_router import RobotAPIRouter

# --- Logging Configuration (Simplified) ---
# Keep it simple for now to ensure basic functionality
LOG_FORMAT = "%(asctime)s.%(msecs)03d - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configure root logger ONLY
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
# --- End Logging Configuration ---

# Create MCP instance
mcp = GausiumMCP("gs-openapi")
router = RobotAPIRouter(mcp)

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

# Define create_robot_command tool
@mcp.tool()
async def create_robot_command(
    serial_number: str, 
    command_type: str,
    command_parameter: Optional[dict] = None
):
    """Creates a robot command.

    Based on: https://developer.gs-robot.com/zh_CN/Robot%20Command%20Service/Create%20Robot%20Command

    Args:
        serial_number: The serial number of the target robot.
        command_type: The type of command (e.g., 'START_TASK', 'PAUSE_TASK', 'STOP_TASK').
        command_parameter: Optional command parameters as a dictionary.

    Returns:
        A dictionary containing the command creation result.
    """
    return await mcp.create_robot_command(
        serial_number=serial_number,
        command_type=command_type,
        command_parameter=command_parameter
    )

# Define get_site_info tool
@mcp.tool()
async def get_site_info(robot_id: str):
    """Gets site information for a specific robot.

    Based on: https://developer.gs-robot.com/zh_CN/Robot%20Task%20Service/Get%20Site%20Info

    Args:
        robot_id: The ID of the target robot.

    Returns:
        A dictionary containing site information including buildings, floors, and maps.
    """
    return await mcp.get_site_info(robot_id=robot_id)

# Define get_map_subareas tool
@mcp.tool()
async def get_map_subareas(map_id: str):
    """Gets map subareas information for precise area control.

    Args:
        map_id: The ID of the target map.

    Returns:
        A dictionary containing map subareas information.
    """
    return await mcp.get_map_subareas(map_id=map_id)

# Define submit_temp_site_task tool
@mcp.tool()
async def submit_temp_site_task(task_data: dict):
    """Submits a temporary task with site information for S-line robots.

    Args:
        task_data: Task data including site, map, and area information.

    Returns:
        A dictionary containing the task submission result.
    """
    return await mcp.submit_temp_site_task(task_data=task_data)

# Define submit_temp_no_site_task tool
@mcp.tool()
async def submit_temp_no_site_task(task_data: dict):
    """Submits a temporary task without site information for S-line robots.

    Args:
        task_data: Task data including map and area information.

    Returns:
        A dictionary containing the task submission result.
    """
    return await mcp.submit_temp_no_site_task(task_data=task_data)


# Define command query tools
@mcp.tool()
async def get_robot_command(serial_number: str, command_id: str):
    """Gets the result of a specific robot command.

    Args:
        serial_number: The serial number of the target robot.
        command_id: The ID of the command to query.

    Returns:
        A dictionary containing the command execution result.
    """
    return await mcp.get_robot_command(serial_number=serial_number, command_id=command_id)

@mcp.tool()
async def list_robot_commands(serial_number: str, page: int = 1, page_size: int = 10):
    """Lists historical commands sent to a robot.

    Args:
        serial_number: The serial number of the target robot.
        page: Page number (default: 1).
        page_size: Number of items per page (default: 10).

    Returns:
        A dictionary containing the historical commands list.
    """
    return await mcp.list_robot_commands(serial_number=serial_number, page=page, page_size=page_size)

# Define map management tools
@mcp.tool()
async def upload_robot_map_v1(map_data: dict):
    """Uploads a robot map using V1 API.

    Args:
        map_data: Map data to upload.

    Returns:
        A dictionary containing the upload result with record_id.
    """
    return await mcp.upload_robot_map_v1(map_data=map_data)

@mcp.tool()
async def get_upload_record_v1(record_id: str):
    """Checks the status of a V1 map upload.

    Args:
        record_id: The upload record ID.

    Returns:
        A dictionary containing the upload status information.
    """
    return await mcp.get_upload_record_v1(record_id=record_id)

@mcp.tool()
async def download_robot_map_v1(map_id: str):
    """Downloads a robot map using V1 API.

    Args:
        map_id: The ID of the map to download.

    Returns:
        A dictionary containing the map download information.
    """
    return await mcp.download_robot_map_v1(map_id=map_id)

@mcp.tool()
async def download_robot_map_v2(map_id: str):
    """Downloads a robot map using V2 API.

    Args:
        map_id: The ID of the map to download.

    Returns:
        A dictionary containing the map download information.
    """
    return await mcp.download_robot_map_v2(map_id=map_id)

# Define task report tools

@mcp.tool()
async def generate_task_report_png(serial_number: str, report_id: str):
    """Generates a PNG map for M-line task report.

    Args:
        serial_number: The serial number of the target robot.
        report_id: The ID of the task report.

    Returns:
        A dictionary containing the map generation result.
    """
    return await mcp.generate_task_report_png(serial_number=serial_number, report_id=report_id)

# Define workflow execution tools
@mcp.tool()
async def execute_m_line_task_workflow(
    serial_number: str,
    task_selection_criteria: Optional[dict] = None
):
    """Executes complete M-line robot task workflow.
    
    Automated process: Status query → Task selection → Command execution

    Args:
        serial_number: The serial number of the target robot.
        task_selection_criteria: Optional task selection criteria.

    Returns:
        A dictionary containing the workflow execution result.
    """
    return await mcp.execute_m_line_task_workflow(
        serial_number=serial_number,
        task_selection_criteria=task_selection_criteria
    )

@mcp.tool()
async def execute_s_line_site_task_workflow(
    robot_id: str,
    task_parameters: dict
):
    """Executes complete S-line robot task workflow with site information.
    
    Automated process: Site info → Map selection → Subarea retrieval → Task building → Task submission

    Args:
        robot_id: The ID of the target robot.
        task_parameters: Task parameters including map criteria and task settings.

    Returns:
        A dictionary containing the workflow execution result.
    """
    return await mcp.execute_s_line_site_task_workflow(
        robot_id=robot_id,
        task_parameters=task_parameters
    )

@mcp.tool()
async def execute_s_line_no_site_task_workflow(
    robot_sn: str,
    task_parameters: dict
):
    """Executes complete S-line robot task workflow without site information.
    
    Automated process: Map list → Map selection → Subarea retrieval → Task building → Task submission

    Args:
        robot_sn: The serial number of the target robot.
        task_parameters: Task parameters including map criteria and task settings.

    Returns:
        A dictionary containing the workflow execution result.
    """
    return await mcp.execute_s_line_no_site_task_workflow(
        robot_sn=robot_sn,
        task_parameters=task_parameters
    )

# --- 智能路由工具 ---

@mcp.tool()
async def get_robot_status_smart(serial_number: str):
    """智能获取机器人状态。
    
    自动根据机器人系列选择V1 (M-line) 或V2 (S-line) API。
    
    Args:
        serial_number: 机器人序列号
        
    Returns:
        机器人状态信息字典
    """
    return await router.get_robot_status_smart(serial_number)

@mcp.tool()
async def get_task_reports_smart(serial_number: str, page: int = 1, page_size: int = 10, 
                                start_time_utc_floor: str = None, start_time_utc_upper: str = None):
    """智能获取任务报告。
    
    自动根据机器人系列选择M-line或S-line任务报告API。
    
    Args:
        serial_number: 机器人序列号
        page: 页码
        page_size: 每页大小
        start_time_utc_floor: 开始时间过滤
        start_time_utc_upper: 结束时间过滤
        
    Returns:
        任务报告数据字典
    """
    kwargs = {"page": page, "page_size": page_size}
    if start_time_utc_floor:
        kwargs["start_time_utc_floor"] = start_time_utc_floor
    if start_time_utc_upper:
        kwargs["start_time_utc_upper"] = start_time_utc_upper
    
    return await router.get_task_reports_smart(serial_number, **kwargs)

@mcp.tool()
async def batch_get_robot_statuses_smart(serial_numbers: list):
    """智能批量获取机器人状态。
    
    自动根据机器人系列分组并选择正确的批量API。
    支持混合查询M-line和S-line机器人。
    
    Args:
        serial_numbers: 机器人序列号列表
        
    Returns:
        批量状态查询结果字典
    """
    return await router.batch_get_robot_statuses_smart(serial_numbers)

@mcp.tool()
async def get_robot_capabilities(serial_number: str):
    """获取机器人支持的API能力。
    
    显示该机器人支持哪些API端点和功能。
    
    Args:
        serial_number: 机器人序列号
        
    Returns:
        机器人能力信息字典
    """
    return await router.get_capabilities(serial_number)

def main():
    """Main entry point for the MCP server."""
    logging.info("Starting Gausium MCP server using mcp.run() with simplified logging...")
    # Run using mcp.run()
    mcp.run(transport='stdio')
    # mcp.run(transport='sse')

if __name__ == "__main__":
    main()

