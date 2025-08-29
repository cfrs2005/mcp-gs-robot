"""
Gausium MCP implementation module.

This module provides the main MCP implementation for the Gausium OpenAPI.
"""

from typing import Any, Dict, Optional, List
from mcp.server.fastmcp import FastMCP

from ..core.client import GausiumAPIClient
from ..workflows.task_engine import TaskExecutionEngine

class GausiumMCP(FastMCP):
    """
    扩展的FastMCP，支持Gausium API。
    
    现在使用统一的API客户端，消除所有重复代码。
    """
    
    def __init__(self, name: str):
        """
        初始化GausiumMCP。
        
        Args:
            name: MCP实例名称
        """
        super().__init__(name)
        # 不再需要直接管理TokenManager，由GausiumAPIClient统一处理
        self.task_engine = TaskExecutionEngine()

    async def list_robots(
        self,
        page: int = 1,
        page_size: int = 10,
        relation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取机器人列表。

        Args:
            page: 页码 (必须 > 0)
            page_size: 每页数量
            relation: 可选关系类型 (例如 'contract')

        Returns:
            包含机器人列表数据的字典

        Raises:
            httpx.HTTPStatusError: API调用返回错误状态码
            httpx.RequestError: 网络连接问题
        """
        query_params = {
            "page": page,
            "pageSize": page_size,
        }
        if relation is not None:
            query_params["relation"] = relation

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'list_robots',
                query_params=query_params
            )

    async def get_robot_status(self, serial_number: str) -> Dict[str, Any]:
        """
        获取特定机器人的状态。

        Args:
            serial_number: 目标机器人的序列号

        Returns:
            包含机器人状态数据的字典

        Raises:
            ValueError: 如果序列号为空
            httpx.HTTPStatusError: API调用返回错误状态码  
            httpx.RequestError: 网络连接问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'get_robot_status',
                path_params={'serial_number': serial_number}
            )

    async def list_robot_task_reports(
        self,
        serial_number: str,
        page: int = 1,
        page_size: int = 100,
        start_time_utc_floor: Optional[str] = None,
        start_time_utc_upper: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取特定机器人的任务报告。

        Args:
            serial_number: 目标机器人的序列号
            page: 页码 (必须 > 0)
            page_size: 每页数量
            start_time_utc_floor: 可选开始时间过滤器 (ISO 8601格式)
            start_time_utc_upper: 可选结束时间过滤器 (ISO 8601格式)

        Returns:
            包含机器人任务报告数据的字典

        Raises:
            ValueError: 如果序列号为空
            httpx.HTTPStatusError: API调用返回错误状态码
            httpx.RequestError: 网络连接问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")

        query_params = {
            "page": page,
            "pageSize": page_size,
        }
        if start_time_utc_floor:
            query_params["startTimeUtcFloor"] = start_time_utc_floor
        if start_time_utc_upper:
            query_params["startTimeUtcUpper"] = start_time_utc_upper

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'list_task_reports',
                path_params={'serial_number': serial_number},
                query_params=query_params
            )

    async def list_robot_maps(self, robot_sn: str) -> List[Dict[str, Any]]:
        """
        获取与特定机器人关联的地图列表。

        Args:
            robot_sn: 目标机器人的序列号

        Returns:
            包含地图ID和地图名称的字典列表

        Raises:
            ValueError: 如果robot_sn为空
            httpx.HTTPStatusError: API调用返回错误状态码
            httpx.RequestError: 网络连接问题
            KeyError: 响应格式异常
        """
        if not robot_sn:
            raise ValueError("Robot serial number cannot be empty")

        async with GausiumAPIClient() as client:
            response = await client.call_endpoint(
                'list_maps',
                json_data={'robotSn': robot_sn}
            )
            
            # 处理Gausium特殊的响应格式
            if response.get('code') == 0:
                return response.get('data', [])
            else:
                raise RuntimeError(f"API returned error: {response.get('msg', 'Unknown error')}")

    async def create_robot_command(
        self,
        serial_number: str,
        command_type: str,
        command_parameter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建机器人指令。

        Args:
            serial_number: 机器人序列号
            command_type: 指令类型 (如 'START_TASK', 'PAUSE_TASK', 等)
            command_parameter: 指令参数

        Returns:
            指令创建结果

        Raises:
            ValueError: 参数无效
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")
        if not command_type:
            raise ValueError("Command type cannot be empty")

        request_data = {
            "serialNumber": serial_number,
            "remoteTaskCommandType": command_type
        }
        
        if command_parameter:
            request_data["commandParameter"] = command_parameter

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'create_command',
                path_params={'serial_number': serial_number},
                json_data=request_data
            )

    async def get_site_info(self, robot_id: str) -> Dict[str, Any]:
        """
        获取站点信息。

        Args:
            robot_id: 机器人ID

        Returns:
            站点信息，包括建筑、楼层和地图

        Raises:
            ValueError: robot_id为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not robot_id:
            raise ValueError("Robot ID cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'get_site_info',
                path_params={'robot_id': robot_id}
            )

    async def get_map_subareas(self, map_id: str) -> Dict[str, Any]:
        """
        获取地图分区信息。

        Args:
            map_id: 地图ID

        Returns:
            地图分区详细信息

        Raises:
            ValueError: map_id为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not map_id:
            raise ValueError("Map ID cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'get_map_subareas',
                path_params={'map_id': map_id}
            )

    async def submit_temp_site_task(
        self,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        S线有站点临时任务下发。

        Args:
            task_data: 任务数据，包含站点、地图、区域等信息

        Returns:
            任务下发结果

        Raises:
            ValueError: 任务数据无效
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not task_data:
            raise ValueError("Task data cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'submit_temp_site_task',
                json_data=task_data
            )

    async def submit_temp_no_site_task(
        self,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        S线无站点临时任务下发。

        Args:
            task_data: 任务数据，包含地图、区域等信息

        Returns:
            任务下发结果

        Raises:
            ValueError: 任务数据无效
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not task_data:
            raise ValueError("Task data cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'submit_temp_no_site_task',
                json_data=task_data
            )

    async def get_robot_status_v1(self, serial_number: str) -> Dict[str, Any]:
        """
        V1获取机器人状态 (40,50,75系列)。

        Args:
            serial_number: 机器人序列号

        Returns:
            V1机器人状态信息

        Raises:
            ValueError: 序列号为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'get_robot_status_v1',
                path_params={'serial_number': serial_number}
            )

    async def batch_get_robot_statuses_v1(
        self, 
        serial_numbers: List[str]
    ) -> Dict[str, Any]:
        """
        V1批量获取机器人状态。

        Args:
            serial_numbers: 机器人序列号列表

        Returns:
            批量状态查询结果

        Raises:
            ValueError: 序列号列表为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_numbers:
            raise ValueError("Serial numbers list cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'batch_get_robot_statuses_v1',
                json_data={'serialNumbers': serial_numbers}
            )

    async def get_robot_status_v2(self, serial_number: str) -> Dict[str, Any]:
        """
        V2获取S,SW机器人状态。

        Args:
            serial_number: 机器人序列号

        Returns:
            V2机器人状态信息

        Raises:
            ValueError: 序列号为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'get_robot_status_v2',
                path_params={'serial_number': serial_number}
            )

    async def batch_get_robot_statuses_v2(
        self, 
        serial_numbers: List[str]
    ) -> Dict[str, Any]:
        """
        V2批量获取S,SW机器人状态。

        Args:
            serial_numbers: 机器人序列号列表

        Returns:
            批量状态查询结果

        Raises:
            ValueError: 序列号列表为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_numbers:
            raise ValueError("Serial numbers list cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'batch_get_robot_statuses_v2',
                json_data={'serialNumbers': serial_numbers}
            )

    async def get_robot_command(
        self, 
        serial_number: str, 
        command_id: str
    ) -> Dict[str, Any]:
        """
        获取单条指令结果。

        Args:
            serial_number: 机器人序列号
            command_id: 指令ID

        Returns:
            指令执行结果

        Raises:
            ValueError: 参数为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")
        if not command_id:
            raise ValueError("Command ID cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'get_command',
                path_params={
                    'serial_number': serial_number,
                    'command_id': command_id
                }
            )

    async def list_robot_commands(
        self,
        serial_number: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        获取机器人历史发出指令。

        Args:
            serial_number: 机器人序列号
            page: 页码，默认1
            page_size: 每页数量，默认10

        Returns:
            历史指令列表

        Raises:
            ValueError: 序列号为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'list_commands',
                path_params={'serial_number': serial_number},
                query_params={
                    'page': page,
                    'pageSize': page_size
                }
            )

    async def upload_robot_map_v1(
        self,
        map_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        V1地图上传。

        Args:
            map_data: 地图数据

        Returns:
            上传结果，包含record_id

        Raises:
            ValueError: 地图数据为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not map_data:
            raise ValueError("Map data cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'upload_map_v1',
                json_data=map_data
            )

    async def get_upload_record_v1(self, record_id: str) -> Dict[str, Any]:
        """
        V1地图上传状态检查。

        Args:
            record_id: 上传记录ID

        Returns:
            上传状态信息

        Raises:
            ValueError: record_id为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not record_id:
            raise ValueError("Record ID cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'get_upload_record_v1',
                path_params={'record_id': record_id}
            )

    async def download_robot_map_v1(self, map_id: str) -> Dict[str, Any]:
        """
        V1获取地图下载。

        Args:
            map_id: 地图ID

        Returns:
            地图下载信息

        Raises:
            ValueError: map_id为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not map_id:
            raise ValueError("Map ID cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'download_map_v1',
                path_params={'map_id': map_id}
            )

    async def download_robot_map_v2(self, map_id: str) -> Dict[str, Any]:
        """
        V2地图下载。

        Args:
            map_id: 地图ID

        Returns:
            地图下载信息

        Raises:
            ValueError: map_id为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not map_id:
            raise ValueError("Map ID cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'download_map_v2',
                path_params={'map_id': map_id}
            )

    async def list_robot_task_reports_s(
        self,
        serial_number: str,
        page: int = 1,
        page_size: int = 100,
        start_time_utc_floor: Optional[str] = None,
        start_time_utc_upper: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        S线任务报告查询。

        Args:
            serial_number: 机器人序列号
            page: 页码，默认1
            page_size: 每页数量，默认100
            start_time_utc_floor: 开始时间过滤器 (ISO 8601格式)
            start_time_utc_upper: 结束时间过滤器 (ISO 8601格式)

        Returns:
            S线任务报告数据

        Raises:
            ValueError: 序列号为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")

        query_params = {
            "page": page,
            "pageSize": page_size,
        }
        if start_time_utc_floor:
            query_params["startTimeUtcFloor"] = start_time_utc_floor
        if start_time_utc_upper:
            query_params["startTimeUtcUpper"] = start_time_utc_upper

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'list_task_reports_s',
                path_params={'serial_number': serial_number},
                query_params=query_params
            )

    async def generate_task_report_png(
        self,
        serial_number: str,
        report_id: str
    ) -> Dict[str, Any]:
        """
        M线任务报告地图生成。

        Args:
            serial_number: 机器人序列号
            report_id: 报告ID

        Returns:
            地图生成结果

        Raises:
            ValueError: 参数为空
            httpx.HTTPStatusError: API调用错误
            httpx.RequestError: 网络问题
        """
        if not serial_number:
            raise ValueError("Serial number cannot be empty")
        if not report_id:
            raise ValueError("Report ID cannot be empty")

        async with GausiumAPIClient() as client:
            return await client.call_endpoint(
                'generate_task_report_png',
                path_params={
                    'serial_number': serial_number,
                    'report_id': report_id
                }
            )

    # 高级工作流方法
    async def execute_m_line_task_workflow(
        self,
        serial_number: str,
        task_selection_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行M线机器人完整任务工作流。
        
        自动化流程：状态查询 → 任务选择 → 指令下发
        
        Args:
            serial_number: 机器人序列号
            task_selection_criteria: 任务选择条件
            
        Returns:
            工作流执行结果
        """
        return await self.task_engine.execute_m_line_task(
            serial_number=serial_number,
            task_selection_criteria=task_selection_criteria
        )

    async def execute_s_line_site_task_workflow(
        self,
        robot_id: str,
        task_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行S线有站点任务完整工作流。
        
        自动化流程：站点信息 → 地图选择 → 分区获取 → 任务构建 → 任务下发
        
        Args:
            robot_id: 机器人ID
            task_parameters: 任务参数
            
        Returns:
            工作流执行结果
        """
        return await self.task_engine.execute_s_line_site_task(
            robot_id=robot_id,
            task_parameters=task_parameters
        )

    async def execute_s_line_no_site_task_workflow(
        self,
        robot_sn: str,
        task_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行S线无站点任务完整工作流。
        
        自动化流程：地图列表 → 地图选择 → 分区获取 → 任务构建 → 任务下发
        
        Args:
            robot_sn: 机器人序列号
            task_parameters: 任务参数
            
        Returns:
            工作流执行结果
        """
        return await self.task_engine.execute_s_line_no_site_task(
            robot_sn=robot_sn,
            task_parameters=task_parameters
        )
