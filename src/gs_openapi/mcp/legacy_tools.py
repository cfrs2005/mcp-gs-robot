"""Opt-in registrations for the original V1/V2 MCP tools."""

from __future__ import annotations

from ..utils.robot_router import RobotAPIRouter
from .gausium_mcp import GausiumMCP


def register_legacy_tools(mcp, gausium_mcp: GausiumMCP, router: RobotAPIRouter) -> None:
    @mcp.tool(name="legacy_list_robots")
    async def list_robots(page: int = 1, page_size: int = 10, relation: str | None = None):
        """Fetch the legacy robot list."""
        return await gausium_mcp.list_robots(page=page, page_size=page_size, relation=relation)

    @mcp.tool(name="legacy_list_robot_maps")
    async def list_robot_maps(robot_sn: str):
        """Fetch the legacy robot map list."""
        return await gausium_mcp.list_robot_maps(robot_sn=robot_sn)

    @mcp.tool(name="legacy_create_robot_command")
    async def create_robot_command(serial_number: str, command_type: str,
                                   command_parameter: dict | None = None):
        """Create a legacy robot command."""
        return await gausium_mcp.create_robot_command(serial_number=serial_number,
            command_type=command_type, command_parameter=command_parameter)

    @mcp.tool(name="legacy_get_site_info")
    async def get_site_info(robot_id: str):
        """Get legacy site information."""
        return await gausium_mcp.get_site_info(robot_id=robot_id)

    @mcp.tool(name="legacy_get_map_subareas")
    async def get_map_subareas(map_id: str):
        """Get legacy map subareas."""
        return await gausium_mcp.get_map_subareas(map_id=map_id)

    @mcp.tool(name="legacy_submit_temp_site_task")
    async def submit_temp_site_task(task_data: dict):
        """Submit a legacy site task."""
        return await gausium_mcp.submit_temp_site_task(task_data=task_data)

    @mcp.tool(name="legacy_submit_temp_no_site_task")
    async def submit_temp_no_site_task(task_data: dict):
        """Submit a legacy no-site task."""
        return await gausium_mcp.submit_temp_no_site_task(task_data=task_data)

    @mcp.tool(name="legacy_get_robot_command")
    async def get_robot_command(serial_number: str, command_id: str):
        """Get a legacy robot command."""
        return await gausium_mcp.get_robot_command(serial_number=serial_number,
                                                    command_id=command_id)

    @mcp.tool(name="legacy_list_robot_commands")
    async def list_robot_commands(serial_number: str, page: int = 1, page_size: int = 10):
        """List legacy robot commands."""
        return await gausium_mcp.list_robot_commands(serial_number=serial_number,
                                                      page=page, page_size=page_size)

    @mcp.tool(name="legacy_upload_robot_map_v1")
    async def upload_robot_map_v1(map_data: dict):
        """Upload a map with the V1 API."""
        return await gausium_mcp.upload_robot_map_v1(map_data=map_data)

    @mcp.tool(name="legacy_get_upload_record_v1")
    async def get_upload_record_v1(record_id: str):
        """Query a V1 map upload."""
        return await gausium_mcp.get_upload_record_v1(record_id=record_id)

    @mcp.tool(name="legacy_download_robot_map_v1")
    async def download_robot_map_v1(map_id: str):
        """Download a map with the V1 API."""
        return await gausium_mcp.download_robot_map_v1(map_id=map_id)

    @mcp.tool(name="legacy_download_robot_map_v2")
    async def download_robot_map_v2(map_id: str):
        """Download a map with the V2 API."""
        return await gausium_mcp.download_robot_map_v2(map_id=map_id)

    @mcp.tool(name="legacy_generate_task_report_png")
    async def generate_task_report_png(serial_number: str, report_id: str):
        """Generate a legacy task report PNG."""
        return await gausium_mcp.generate_task_report_png(serial_number=serial_number,
                                                           report_id=report_id)

    @mcp.tool(name="legacy_execute_m_line_task_workflow")
    async def execute_m_line_task_workflow(serial_number: str,
                                            task_selection_criteria: dict | None = None):
        """Execute the M-line legacy task workflow."""
        return await gausium_mcp.execute_m_line_task_workflow(
            serial_number=serial_number, task_selection_criteria=task_selection_criteria)

    @mcp.tool(name="legacy_execute_s_line_site_task_workflow")
    async def execute_s_line_site_task_workflow(robot_id: str, task_parameters: dict):
        """Execute the S-line legacy site workflow."""
        return await gausium_mcp.execute_s_line_site_task_workflow(
            robot_id=robot_id, task_parameters=task_parameters)

    @mcp.tool(name="legacy_execute_s_line_no_site_task_workflow")
    async def execute_s_line_no_site_task_workflow(robot_sn: str, task_parameters: dict):
        """Execute the S-line legacy no-site workflow."""
        return await gausium_mcp.execute_s_line_no_site_task_workflow(
            robot_sn=robot_sn, task_parameters=task_parameters)

    @mcp.tool(name="legacy_get_robot_status_smart")
    async def get_robot_status_smart(serial_number: str):
        """Route legacy robot status by robot family."""
        return await router.get_robot_status_smart(serial_number)

    @mcp.tool(name="legacy_get_task_reports_smart")
    async def get_task_reports_smart(serial_number: str, page: int = 1, page_size: int = 10,
                                      start_time_utc_floor: str | None = None,
                                      start_time_utc_upper: str | None = None):
        """Route legacy report queries by robot family."""
        kwargs = {"page": page, "page_size": page_size}
        if start_time_utc_floor:
            kwargs["start_time_utc_floor"] = start_time_utc_floor
        if start_time_utc_upper:
            kwargs["start_time_utc_upper"] = start_time_utc_upper
        return await router.get_task_reports_smart(serial_number, **kwargs)

    @mcp.tool(name="legacy_batch_get_robot_statuses_smart")
    async def batch_get_robot_statuses_smart(serial_numbers: list):
        """Batch query legacy robot status by family."""
        return await router.batch_get_robot_statuses_smart(serial_numbers)

    @mcp.tool(name="legacy_get_robot_capabilities")
    async def get_robot_capabilities(serial_number: str):
        """Get legacy robot API capabilities."""
        return await router.get_capabilities(serial_number)
