"""
API端点配置定义。

使用数据驱动的方式定义所有API端点，消除代码中的魔法字符串和特殊情况。
遵循Linus原则：用数据结构解决问题，而不是代码逻辑。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class HTTPMethod(Enum):
    """HTTP方法枚举。"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class APIVersion(Enum):
    """API版本枚举。"""
    V1_ALPHA1 = "v1alpha1"
    V2_ALPHA1 = "v2alpha1" 
    V1 = "v1"
    GAS_V1_ALPHA1 = "gas/api/v1alpha1"
    OPENAPI_V1 = "openapi/v1"
    OPENAPI_V2_ALPHA1 = "openapi/v2alpha1"


@dataclass(frozen=True)
class APIEndpoint:
    """
    API端点定义。
    
    使用不可变数据类确保端点配置的一致性。
    """
    name: str
    path: str
    method: HTTPMethod
    version: APIVersion
    requires_auth: bool = True
    description: str = ""
    
    @property
    def full_path(self) -> str:
        """构建完整的API路径。"""
        return f"/{self.version.value}/{self.path}" if not self.path.startswith('/') else f"/{self.version.value}{self.path}"


# 认证服务端点
AUTH_ENDPOINTS = {
    'get_token': APIEndpoint(
        name="get_oauth_token",
        path="oauth/token",
        method=HTTPMethod.POST,
        version=APIVersion.GAS_V1_ALPHA1,
        requires_auth=False,
        description="获取OAuth访问令牌"
    ),
    'refresh_token': APIEndpoint(
        name="refresh_oauth_token", 
        path="oauth/token",
        method=HTTPMethod.POST,
        version=APIVersion.GAS_V1_ALPHA1,
        requires_auth=False,
        description="刷新OAuth访问令牌"
    )
}

# 机器人信息服务端点
ROBOT_INFO_ENDPOINTS = {
    'list_robots': APIEndpoint(
        name="list_robots",
        path="robots",
        method=HTTPMethod.GET,
        version=APIVersion.V1_ALPHA1,
        description="列出机器人"
    ),
    'get_robot_status': APIEndpoint(
        name="get_robot_status",
        path="robots/{serial_number}/status",
        method=HTTPMethod.GET,
        version=APIVersion.V1_ALPHA1,
        description="获取机器人状态 (基础版本)"
    ),
    'get_robot_status_v1': APIEndpoint(
        name="get_robot_status_v1",
        path="robots/{serial_number}/status",
        method=HTTPMethod.GET,
        version=APIVersion.V1_ALPHA1,
        description="V1获取机器人状态 (40,50,75系列)"
    ),
    'batch_get_robot_statuses_v1': APIEndpoint(
        name="batch_get_robot_statuses_v1", 
        path="robots/batch/status",
        method=HTTPMethod.POST,
        version=APIVersion.V1_ALPHA1,
        description="V1批量获取机器人状态"
    ),
    'get_robot_status_v2': APIEndpoint(
        name="get_robot_status_v2",
        path="s/robots/{serial_number}/status",
        method=HTTPMethod.GET,
        version=APIVersion.OPENAPI_V2_ALPHA1,
        description="V2获取S,SW机器人状态"
    ),
    'batch_get_robot_statuses_v2': APIEndpoint(
        name="batch_get_robot_statuses_v2",
        path="s/robots/batch/status", 
        method=HTTPMethod.POST,
        version=APIVersion.OPENAPI_V2_ALPHA1,
        description="V2批量获取S,SW机器人状态"
    )
}

# 机器人任务服务端点
ROBOT_TASK_ENDPOINTS = {
    'get_site_info': APIEndpoint(
        name="get_site_info",
        path="robots/{robot_id}/getSiteInfo", 
        method=HTTPMethod.GET,
        version=APIVersion.OPENAPI_V2_ALPHA1,
        description="获取站点信息"
    ),
    'submit_temp_site_task': APIEndpoint(
        name="submit_temp_site_task",
        path="tasks/temporary/site",
        method=HTTPMethod.POST,
        version=APIVersion.V1_ALPHA1,
        description="S线有站点临时任务下发"
    ),
    'submit_temp_no_site_task': APIEndpoint(
        name="submit_temp_no_site_task", 
        path="tasks/temporary/no-site",
        method=HTTPMethod.POST,
        version=APIVersion.V1_ALPHA1,
        description="S线无站点临时任务下发"
    )
}

# 机器人指令服务端点  
ROBOT_COMMAND_ENDPOINTS = {
    'create_command': APIEndpoint(
        name="create_robot_command",
        path="robots/{serial_number}/commands",
        method=HTTPMethod.POST,
        version=APIVersion.V1_ALPHA1,
        description="创建机器人指令"
    ),
    'get_command': APIEndpoint(
        name="get_robot_command",
        path="robots/{serial_number}/commands/{command_id}",
        method=HTTPMethod.GET,
        version=APIVersion.V1_ALPHA1,
        description="获取单条指令结果"
    ),
    'list_commands': APIEndpoint(
        name="list_robot_commands",
        path="robots/{serial_number}/commands",
        method=HTTPMethod.GET,
        version=APIVersion.V1_ALPHA1,
        description="获取机器人历史发出指令"
    )
}

# 机器人地图服务端点
ROBOT_MAP_ENDPOINTS = {
    'list_maps': APIEndpoint(
        name="list_robot_maps",
        path="map/robotMap/list",
        method=HTTPMethod.POST,
        version=APIVersion.OPENAPI_V1,
        description="V1列出机器人地图"
    ),
    'get_map_subareas': APIEndpoint(
        name="get_map_subareas",
        path="map/{map_id}/subareas",
        method=HTTPMethod.GET,
        version=APIVersion.OPENAPI_V2_ALPHA1,
        description="查询机器人地图分区"
    ),
    'upload_map_v1': APIEndpoint(
        name="upload_robot_map_v1",
        path="map/upload",
        method=HTTPMethod.POST,
        version=APIVersion.OPENAPI_V1,
        description="V1地图上传"
    ),
    'get_upload_record_v1': APIEndpoint(
        name="get_upload_record_v1",
        path="map/upload/{record_id}",
        method=HTTPMethod.GET,
        version=APIVersion.OPENAPI_V1,
        description="V1地图上传状态检查"
    ),
    'download_map_v1': APIEndpoint(
        name="download_robot_map_v1",
        path="map/{map_id}/download",
        method=HTTPMethod.GET,
        version=APIVersion.OPENAPI_V1,
        description="V1获取地图下载"
    ),
    'download_map_v2': APIEndpoint(
        name="download_robot_map_v2",
        path="map/{map_id}/download",
        method=HTTPMethod.GET,
        version=APIVersion.OPENAPI_V2_ALPHA1,
        description="V2地图下载"
    )
}

# 机器人清洁数据服务端点
ROBOT_CLEANING_ENDPOINTS = {
    'list_task_reports_m': APIEndpoint(
        name="list_robot_task_reports_m",
        path="robots/{serial_number}/taskReports",
        method=HTTPMethod.GET,
        version=APIVersion.V1_ALPHA1,
        description="M线任务报告"
    ),
    'generate_task_report_png': APIEndpoint(
        name="generate_task_report_png",
        path="robots/{serial_number}/taskReports/{report_id}/map",
        method=HTTPMethod.GET,
        version=APIVersion.V1_ALPHA1,
        description="M线任务报告地图生成"
    ),
    'list_task_reports_s': APIEndpoint(
        name="list_robot_task_reports_s",
        path="robots/{serial_number}/taskReports",
        method=HTTPMethod.GET,
        version=APIVersion.OPENAPI_V2_ALPHA1,
        description="S线任务报告"
    )
}

# 所有端点的统一注册表
ALL_ENDPOINTS: Dict[str, APIEndpoint] = {
    **AUTH_ENDPOINTS,
    **ROBOT_INFO_ENDPOINTS,
    **ROBOT_TASK_ENDPOINTS,
    **ROBOT_COMMAND_ENDPOINTS,
    **ROBOT_MAP_ENDPOINTS,
    **ROBOT_CLEANING_ENDPOINTS
}


def get_endpoint(name: str) -> APIEndpoint:
    """
    根据名称获取端点配置。
    
    Args:
        name: 端点名称
        
    Returns:
        端点配置对象
        
    Raises:
        KeyError: 端点不存在
    """
    if name not in ALL_ENDPOINTS:
        available = list(ALL_ENDPOINTS.keys())
        raise KeyError(f"Endpoint '{name}' not found. Available: {available}")
    return ALL_ENDPOINTS[name]


def format_path(endpoint: APIEndpoint, **kwargs) -> str:
    """
    格式化端点路径，替换路径参数。
    
    Args:
        endpoint: 端点配置
        **kwargs: 路径参数
        
    Returns:
        格式化后的完整路径
    """
    path = endpoint.full_path
    for key, value in kwargs.items():
        path = path.replace(f"{{{key}}}", str(value))
    return path