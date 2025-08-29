"""
任务执行工作流引擎。

实现M线和S线机器人的完整任务执行工作流。
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from ..core.client import GausiumAPIClient

logger = logging.getLogger(__name__)


class RobotLineType(Enum):
    """机器人产品线类型。"""
    M_LINE = "m_line"  # M线: 40, 50, 75系列
    S_LINE = "s_line"  # S线
    SW_LINE = "sw_line"  # SW线


class TaskExecutionEngine:
    """
    任务执行工作流引擎。
    
    根据不同的机器人产品线，实现相应的任务执行工作流。
    """
    
    def __init__(self):
        """初始化任务执行引擎。"""
        pass
    
    async def execute_m_line_task(
        self,
        serial_number: str,
        task_selection_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行M线机器人任务。
        
        工作流：
        1. 获取机器人状态
        2. 从状态中提取可执行任务列表
        3. 根据条件选择任务
        4. 通过Create Robot Command下发任务
        
        Args:
            serial_number: 机器人序列号
            task_selection_criteria: 任务选择条件
            
        Returns:
            任务执行结果
        """
        logger.info(f"Starting M-line task execution for robot: {serial_number}")
        
        async with GausiumAPIClient() as client:
            try:
                # 1. 获取机器人状态
                status = await client.call_endpoint(
                    'get_robot_status_v1',
                    path_params={'serial_number': serial_number}
                )
                
                # 2. 解析可执行任务列表
                available_tasks = self._extract_m_line_tasks(status)
                if not available_tasks:
                    raise ValueError("No executable tasks found in robot status")
                
                # 3. 选择任务
                selected_task = self._select_m_line_task(
                    available_tasks, 
                    task_selection_criteria or {}
                )
                
                # 4. 构建并下发任务指令
                command_result = await client.call_endpoint(
                    'create_command',
                    path_params={'serial_number': serial_number},
                    json_data={
                        "serialNumber": serial_number,
                        "remoteTaskCommandType": "START_TASK",
                        "commandParameter": {
                            "startTaskParameter": selected_task
                        }
                    }
                )
                
                logger.info(f"M-line task executed successfully: {command_result}")
                return command_result
                
            except Exception as e:
                logger.error(f"M-line task execution failed: {str(e)}")
                raise

    async def execute_s_line_site_task(
        self,
        robot_id: str,
        task_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行S线有站点任务。
        
        工作流：
        1. 获取站点信息
        2. 解析可用地图
        3. 获取目标地图分区
        4. 构建并下发有站点临时任务
        
        Args:
            robot_id: 机器人ID
            task_parameters: 任务参数
            
        Returns:
            任务执行结果
        """
        logger.info(f"Starting S-line site task execution for robot: {robot_id}")
        
        async with GausiumAPIClient() as client:
            try:
                # 1. 获取站点信息
                site_info = await client.call_endpoint(
                    'get_site_info',
                    path_params={'robot_id': robot_id}
                )
                
                # 2. 解析可用地图
                available_maps = self._extract_maps_from_site(site_info)
                if not available_maps:
                    raise ValueError("No maps found in site information")
                
                # 3. 选择目标地图
                target_map_id = self._select_map(
                    available_maps, 
                    task_parameters.get('map_criteria', {})
                )
                
                # 4. 获取地图分区
                subareas = await client.call_endpoint(
                    'get_map_subareas',
                    path_params={'map_id': target_map_id}
                )
                
                # 5. 构建任务数据
                task_data = self._build_site_task_data(
                    target_map_id, 
                    subareas, 
                    task_parameters
                )
                
                # 6. 下发有站点临时任务
                task_result = await client.call_endpoint(
                    'submit_temp_site_task',
                    json_data=task_data
                )
                
                logger.info(f"S-line site task executed successfully: {task_result}")
                return task_result
                
            except Exception as e:
                logger.error(f"S-line site task execution failed: {str(e)}")
                raise

    async def execute_s_line_no_site_task(
        self,
        robot_sn: str,
        task_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行S线无站点任务。
        
        工作流：
        1. 获取机器人地图列表
        2. 获取目标地图分区
        3. 构建并下发无站点临时任务
        
        Args:
            robot_sn: 机器人序列号
            task_parameters: 任务参数
            
        Returns:
            任务执行结果
        """
        logger.info(f"Starting S-line no-site task execution for robot: {robot_sn}")
        
        async with GausiumAPIClient() as client:
            try:
                # 1. 获取机器人地图列表
                maps_response = await client.call_endpoint(
                    'list_maps',
                    json_data={'robotSn': robot_sn}
                )
                
                # 处理Gausium特殊响应格式
                if maps_response.get('code') != 0:
                    raise RuntimeError(f"Failed to get maps: {maps_response.get('msg')}")
                
                available_maps = maps_response.get('data', [])
                if not available_maps:
                    raise ValueError("No maps found for robot")
                
                # 2. 选择目标地图
                target_map_id = self._select_map_from_list(
                    available_maps,
                    task_parameters.get('map_criteria', {})
                )
                
                # 3. 获取地图分区
                subareas = await client.call_endpoint(
                    'get_map_subareas',
                    path_params={'map_id': target_map_id}
                )
                
                # 4. 构建任务数据
                task_data = self._build_no_site_task_data(
                    target_map_id,
                    subareas,
                    task_parameters
                )
                
                # 5. 下发无站点临时任务
                task_result = await client.call_endpoint(
                    'submit_temp_no_site_task',
                    json_data=task_data
                )
                
                logger.info(f"S-line no-site task executed successfully: {task_result}")
                return task_result
                
            except Exception as e:
                logger.error(f"S-line no-site task execution failed: {str(e)}")
                raise

    def _extract_m_line_tasks(self, robot_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从M线机器人状态中提取可执行任务列表。
        
        Args:
            robot_status: 机器人状态信息
            
        Returns:
            可执行任务列表
        """
        # TODO: 根据实际API响应格式实现
        # 这里需要根据实际的机器人状态响应格式来解析任务列表
        tasks = robot_status.get('available_tasks', [])
        if not tasks:
            # 如果没有直接的任务列表，尝试从其他字段解析
            # 需要根据实际响应格式调整
            logger.warning("No 'available_tasks' field found in robot status")
        
        return tasks

    def _select_m_line_task(
        self, 
        available_tasks: List[Dict[str, Any]], 
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据条件选择M线任务。
        
        Args:
            available_tasks: 可用任务列表
            criteria: 选择条件
            
        Returns:
            选中的任务
        """
        if not criteria:
            # 如果没有指定条件，返回第一个任务
            return available_tasks[0]
        
        # TODO: 实现更复杂的任务选择逻辑
        # 可以根据任务名称、地图、清洁模式等条件筛选
        for task in available_tasks:
            if self._matches_criteria(task, criteria):
                return task
        
        # 如果没有匹配的任务，返回第一个
        return available_tasks[0]

    def _extract_maps_from_site(self, site_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从站点信息中提取地图列表。
        
        Args:
            site_info: 站点信息
            
        Returns:
            地图列表
        """
        maps = []
        buildings = site_info.get('buildings', [])
        
        for building in buildings:
            floors = building.get('floors', [])
            for floor in floors:
                floor_maps = floor.get('maps', [])
                if isinstance(floor_maps, list):
                    maps.extend(floor_maps)
        
        return maps

    def _select_map(
        self, 
        available_maps: List[Dict[str, Any]], 
        criteria: Dict[str, Any]
    ) -> str:
        """
        选择目标地图。
        
        Args:
            available_maps: 可用地图列表
            criteria: 选择条件
            
        Returns:
            选中的地图ID
        """
        if not criteria:
            return available_maps[0].get('mapId') or available_maps[0].get('id')
        
        # TODO: 实现地图选择逻辑
        for map_info in available_maps:
            if self._matches_criteria(map_info, criteria):
                return map_info.get('mapId') or map_info.get('id')
        
        # 默认返回第一个地图
        return available_maps[0].get('mapId') or available_maps[0].get('id')

    def _select_map_from_list(
        self,
        available_maps: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> str:
        """
        从地图列表中选择目标地图。
        
        Args:
            available_maps: 可用地图列表  
            criteria: 选择条件
            
        Returns:
            选中的地图ID
        """
        if not criteria:
            return available_maps[0]['mapId']
        
        # TODO: 实现地图选择逻辑
        for map_info in available_maps:
            if self._matches_criteria(map_info, criteria):
                return map_info['mapId']
        
        return available_maps[0]['mapId']

    def _build_site_task_data(
        self,
        map_id: str,
        subareas: Dict[str, Any],
        task_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        构建有站点任务数据。
        
        Args:
            map_id: 地图ID
            subareas: 地图分区信息
            task_parameters: 任务参数
            
        Returns:
            任务数据
        """
        # TODO: 根据实际API要求构建任务数据
        task_data = {
            "mapId": map_id,
            "subareas": subareas,
            "taskType": task_parameters.get('task_type', 'cleaning'),
            "cleaningMode": task_parameters.get('cleaning_mode', '__middle_cleaning'),
            **task_parameters
        }
        
        return task_data

    def _build_no_site_task_data(
        self,
        map_id: str,
        subareas: Dict[str, Any],
        task_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        构建无站点任务数据。
        
        Args:
            map_id: 地图ID
            subareas: 地图分区信息
            task_parameters: 任务参数
            
        Returns:
            任务数据
        """
        # TODO: 根据实际API要求构建任务数据
        task_data = {
            "mapId": map_id,
            "subareas": subareas,
            "taskType": task_parameters.get('task_type', 'cleaning'),
            "cleaningMode": task_parameters.get('cleaning_mode', '__middle_cleaning'),
            **task_parameters
        }
        
        return task_data

    def _matches_criteria(
        self, 
        item: Dict[str, Any], 
        criteria: Dict[str, Any]
    ) -> bool:
        """
        检查项目是否匹配选择条件。
        
        Args:
            item: 要检查的项目
            criteria: 匹配条件
            
        Returns:
            是否匹配
        """
        for key, value in criteria.items():
            if key in item and item[key] != value:
                return False
        return True