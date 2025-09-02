"""
机器人API智能路由工具。

根据机器人系列自动选择正确的API版本和端点。
"""

from typing import Dict, Any, Optional, List
from ..mcp.gausium_mcp import GausiumMCP

class RobotAPIRouter:
    """机器人API智能路由器。
    
    根据机器人序列号前缀自动路由到正确的API版本：
    - M-line: GS100/GS500 (75系列), GS301/GS401 (50系列), GS442 (40系列)
    - S-line: GS438/GS408 (S系列), GS43C (SW系列)
    - 默认: 未知前缀使用V1 API
    """
    
    # 机器人系列前缀映射
    ROBOT_SERIES_MAPPING = {
        # M-line 机器人
        "GS100": "75",    # 75系列
        "GS400": "75",    # 75系列 (新发现)
        "GS500": "75",    # 75系列
        "GS301": "50",    # 50系列
        "GS401": "50",    # 50系列  
        "GS501": "50",    # 50系列 (新发现)
        "GS442": "40",    # 40系列
        
        # S-line 机器人
        "GS438": "S",     # S系列
        "GS408": "S",     # S系列
        "GS43C": "SW",    # SW系列
    }
    
    def __init__(self, mcp: GausiumMCP):
        self.mcp = mcp
        self._robot_cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_robot_info(self, serial_number: str) -> Optional[Dict[str, Any]]:
        """获取机器人基本信息（带缓存）。"""
        if serial_number in self._robot_cache:
            return self._robot_cache[serial_number]
        
        try:
            # 从机器人列表中查找
            robots_response = await self.mcp.list_robots(page=1, page_size=100, relation="bound")
            
            for robot in robots_response.get("robots", []):
                if robot["serialNumber"] == serial_number:
                    self._robot_cache[serial_number] = robot
                    return robot
            
            # 如果第一页没找到，搜索更多页面
            total = int(robots_response.get("total", "0"))
            pages_needed = (total + 99) // 100  # 向上取整
            
            for page in range(2, min(pages_needed + 1, 20)):  # 最多搜索20页
                robots_response = await self.mcp.list_robots(page=page, page_size=100, relation="bound")
                for robot in robots_response.get("robots", []):
                    if robot["serialNumber"] == serial_number:
                        self._robot_cache[serial_number] = robot
                        return robot
        except Exception as e:
            print(f"Failed to get robot info for {serial_number}: {e}")
        
        return None
    
    def _determine_robot_series_from_sn(self, serial_number: str) -> str:
        """根据序列号前缀判断机器人系列。
        
        Args:
            serial_number: 机器人序列号
            
        Returns:
            机器人系列代码 (40, 50, 75, S, SW) 或 "unknown"
        """
        if len(serial_number) < 5:
            return "unknown"
        
        prefix = serial_number[:5]
        return self.ROBOT_SERIES_MAPPING.get(prefix, "unknown")
    
    def is_m_line_robot(self, model_family_code: str) -> bool:
        """判断是否为M-line机器人。"""
        return model_family_code in ["40", "50", "75", "OMNIE"]
    
    def is_s_line_robot(self, model_family_code: str) -> bool:
        """判断是否为S-line机器人。"""
        return model_family_code in ["S", "SW"]
    
    async def get_robot_status_smart(self, serial_number: str) -> Dict[str, Any]:
        """智能获取机器人状态。
        
        自动根据机器人序列号前缀选择V1或V2 API。
        """
        # 基于序列号前缀判断机器人系列
        detected_series = self._determine_robot_series_from_sn(serial_number)
        
        if self.is_s_line_robot(detected_series):
            # S-line 机器人使用 V2 API
            result = await self.mcp.get_robot_status_v2(serial_number)
            result["api_version"] = "V2 (S-line)"
            result["detected_series"] = detected_series
            return result
        else:
            # M-line 机器人或未知类型默认使用 V1 API
            result = await self.mcp.get_robot_status_v1(serial_number)
            result["api_version"] = "V1 (M-line/Default)"
            result["detected_series"] = detected_series
            return result
    
    async def get_task_reports_smart(self, serial_number: str, **kwargs) -> Dict[str, Any]:
        """智能获取任务报告。
        
        自动根据机器人序列号前缀选择M-line或S-line任务报告API。
        """
        # 基于序列号前缀判断机器人系列
        detected_series = self._determine_robot_series_from_sn(serial_number)
        
        if self.is_s_line_robot(detected_series):
            # S-line 机器人使用专用任务报告API
            result = await self.mcp.list_robot_task_reports_s(serial_number, **kwargs)
            result["api_version"] = "S-line API"
            result["detected_series"] = detected_series
            return result
        else:
            # M-line 机器人或未知类型使用默认任务报告API
            result = await self.mcp.list_robot_task_reports(serial_number, **kwargs)
            result["api_version"] = "M-line/Default API"
            result["detected_series"] = detected_series
            return result

    async def batch_get_robot_statuses_smart(self, serial_numbers: List[str]) -> Dict[str, Any]:
        """智能批量获取机器人状态。
        
        自动根据机器人序列号前缀分组并选择正确的批量API。
        """
        if not serial_numbers:
            return {"results": []}
        
        # 按机器人系列分组（基于序列号前缀）
        m_line_robots = []
        s_line_robots = []
        unknown_robots = []
        
        for serial_number in serial_numbers:
            detected_series = self._determine_robot_series_from_sn(serial_number)
            
            if self.is_s_line_robot(detected_series):
                s_line_robots.append(serial_number)
            elif self.is_m_line_robot(detected_series):
                m_line_robots.append(serial_number)
            else:
                # 未知前缀默认归类为M-line (使用V1 API)
                unknown_robots.append(serial_number)
        
        results = []
        
        # 合并M-line机器人和未知机器人，都用V1 API
        v1_robots = m_line_robots + unknown_robots
        
        # 批量查询V1 API机器人状态
        if v1_robots:
            try:
                v1_results = await self.mcp.batch_get_robot_statuses_v1(v1_robots)
                if isinstance(v1_results, dict) and "results" in v1_results:
                    for result in v1_results["results"]:
                        result["api_version"] = "V1 (M-line/Default)"
                        result["detected_series"] = self._determine_robot_series_from_sn(result.get("serialNumber", ""))
                    results.extend(v1_results["results"])
                else:
                    results.extend(v1_results if isinstance(v1_results, list) else [v1_results])
            except Exception as e:
                for sn in v1_robots:
                    results.append({
                        "serialNumber": sn, 
                        "error": str(e), 
                        "robotType": "V1 API",
                        "detected_series": self._determine_robot_series_from_sn(sn)
                    })
        
        # 批量查询S-line机器人状态
        if s_line_robots:
            try:
                s_results = await self.mcp.batch_get_robot_statuses_v2(s_line_robots)
                if isinstance(s_results, dict) and "results" in s_results:
                    for result in s_results["results"]:
                        result["api_version"] = "V2 (S-line)"
                        result["detected_series"] = self._determine_robot_series_from_sn(result.get("serialNumber", ""))
                    results.extend(s_results["results"])
                else:
                    results.extend(s_results if isinstance(s_results, list) else [s_results])
            except Exception as e:
                for sn in s_line_robots:
                    results.append({
                        "serialNumber": sn, 
                        "error": str(e), 
                        "robotType": "V2 API",
                        "detected_series": self._determine_robot_series_from_sn(sn)
                    })
        
        return {
            "total": len(serial_numbers),
            "v1_count": len(v1_robots),
            "s_line_count": len(s_line_robots),
            "results": results
        }
    
    async def get_capabilities(self, serial_number: str) -> Dict[str, Any]:
        """获取机器人支持的API能力。"""
        # 基于序列号前缀判断机器人系列
        detected_series = self._determine_robot_series_from_sn(serial_number)
        
        capabilities = {
            "basic_status": True,
            "command_control": True,
            "task_reports": True,
            "maps": True,
            "site_info": False,
            "advanced_tasks": False
        }
        
        if self.is_s_line_robot(detected_series):
            capabilities.update({
                "site_info": True,
                "advanced_tasks": True,
                "v2_status": True,
                "v1_status": False
            })
            robot_series = "S-line"
        elif self.is_m_line_robot(detected_series):
            capabilities.update({
                "v1_status": True,
                "v2_status": False,
                "command_control": True
            })
            robot_series = "M-line"
        else:
            # 未知前缀默认使用V1 API
            capabilities.update({
                "v1_status": True,
                "v2_status": False,
                "command_control": True
            })
            robot_series = "Unknown (Default V1)"
        
        return {
            "serial_number": serial_number,
            "robot_series": robot_series,
            "detected_series": detected_series,
            "prefix": serial_number[:5] if len(serial_number) >= 5 else serial_number,
            "capabilities": capabilities
        }