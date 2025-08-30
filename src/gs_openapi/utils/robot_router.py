"""
机器人API智能路由工具。

根据机器人系列自动选择正确的API版本和端点。
"""

from typing import Dict, Any, Optional, List
from ..mcp.gausium_mcp import GausiumMCP

class RobotAPIRouter:
    """机器人API智能路由器。
    
    根据机器人系列(modelFamilyCode)自动路由到正确的API版本：
    - M-line (40, 50, 75, OMNIE): 使用V1 API
    - S-line (S, SW): 使用V2 API
    """
    
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
    
    def is_m_line_robot(self, model_family_code: str) -> bool:
        """判断是否为M-line机器人。"""
        return model_family_code in ["40", "50", "75", "OMNIE"]
    
    def is_s_line_robot(self, model_family_code: str) -> bool:
        """判断是否为S-line机器人。"""
        return model_family_code in ["S", "SW"]
    
    async def get_robot_status_smart(self, serial_number: str) -> Dict[str, Any]:
        """智能获取机器人状态。
        
        自动根据机器人系列选择V1或V2 API。
        """
        robot_info = await self.get_robot_info(serial_number)
        if not robot_info:
            raise ValueError(f"Robot {serial_number} not found")
        
        model_family = robot_info.get("modelFamilyCode", "")
        
        if self.is_m_line_robot(model_family):
            return await self.mcp.get_robot_status_v1(serial_number)
        elif self.is_s_line_robot(model_family):
            return await self.mcp.get_robot_status_v2(serial_number)
        else:
            raise ValueError(f"Unknown robot family: {model_family} for robot {serial_number}")
    
    async def get_task_reports_smart(self, serial_number: str, **kwargs) -> Dict[str, Any]:
        """智能获取任务报告。
        
        自动根据机器人系列选择M-line或S-line任务报告API。
        """
        robot_info = await self.get_robot_info(serial_number)
        if not robot_info:
            raise ValueError(f"Robot {serial_number} not found")
        
        model_family = robot_info.get("modelFamilyCode", "")
        
        if self.is_m_line_robot(model_family):
            # M-line使用基础任务报告API
            return await self.mcp.list_robot_task_reports(serial_number, **kwargs)
        elif self.is_s_line_robot(model_family):
            return await self.mcp.list_robot_task_reports_s(serial_number, **kwargs)
        else:
            raise ValueError(f"Unknown robot family: {model_family} for robot {serial_number}")

    async def batch_get_robot_statuses_smart(self, serial_numbers: List[str]) -> Dict[str, Any]:
        """智能批量获取机器人状态。
        
        自动根据机器人系列分组并选择正确的批量API。
        """
        if not serial_numbers:
            return {"results": []}
        
        # 按机器人系列分组
        m_line_robots = []
        s_line_robots = []
        unknown_robots = []
        
        for serial_number in serial_numbers:
            robot_info = await self.get_robot_info(serial_number)
            if not robot_info:
                unknown_robots.append(serial_number)
                continue
            
            model_family = robot_info.get("modelFamilyCode", "")
            if self.is_m_line_robot(model_family):
                m_line_robots.append(serial_number)
            elif self.is_s_line_robot(model_family):
                s_line_robots.append(serial_number)
            else:
                unknown_robots.append(serial_number)
        
        results = []
        
        # 批量查询M-line机器人状态
        if m_line_robots:
            try:
                m_results = await self.mcp.batch_get_robot_statuses_v1(m_line_robots)
                if isinstance(m_results, dict) and "results" in m_results:
                    results.extend(m_results["results"])
                else:
                    results.extend(m_results if isinstance(m_results, list) else [m_results])
            except Exception as e:
                for sn in m_line_robots:
                    results.append({"serialNumber": sn, "error": str(e), "robotType": "M-line"})
        
        # 批量查询S-line机器人状态
        if s_line_robots:
            try:
                s_results = await self.mcp.batch_get_robot_statuses_v2(s_line_robots)
                if isinstance(s_results, dict) and "results" in s_results:
                    results.extend(s_results["results"])
                else:
                    results.extend(s_results if isinstance(s_results, list) else [s_results])
            except Exception as e:
                for sn in s_line_robots:
                    results.append({"serialNumber": sn, "error": str(e), "robotType": "S-line"})
        
        # 处理未知机器人
        for sn in unknown_robots:
            results.append({"serialNumber": sn, "error": "Robot not found or unknown series", "robotType": "Unknown"})
        
        return {
            "total": len(serial_numbers),
            "m_line_count": len(m_line_robots),
            "s_line_count": len(s_line_robots),
            "unknown_count": len(unknown_robots),
            "results": results
        }
    
    async def get_capabilities(self, serial_number: str) -> Dict[str, bool]:
        """获取机器人支持的API能力。"""
        robot_info = await self.get_robot_info(serial_number)
        if not robot_info:
            return {"error": True, "message": f"Robot {serial_number} not found"}
        
        model_family = robot_info.get("modelFamilyCode", "")
        
        capabilities = {
            "basic_status": True,
            "command_control": True,
            "task_reports": True,
            "maps": False,  # 地图API需要修复
            "site_info": False,
            "advanced_tasks": False
        }
        
        if self.is_s_line_robot(model_family):
            capabilities.update({
                "site_info": True,
                "advanced_tasks": True,
                "v2_status": True,
                "v1_status": False
            })
        elif self.is_m_line_robot(model_family):
            capabilities.update({
                "v1_status": True,
                "v2_status": False,
                "command_control": True
            })
        
        return {
            "robot_series": "S-line" if self.is_s_line_robot(model_family) else "M-line" if self.is_m_line_robot(model_family) else "Unknown",
            "model_family": model_family,
            "capabilities": capabilities
        }