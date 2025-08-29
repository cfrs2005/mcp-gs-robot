"""
统一的Gausium API客户端实现。

这个模块实现Linus原则：
1. 消除特殊情况 - 所有API调用使用统一方法
2. 好品味的设计 - 单一职责，明确边界
3. 简洁性 - 不超过3层缩进
"""

import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from ..auth.token_manager import TokenManager
from ..config import GAUSIUM_BASE_URL
from .endpoints import APIEndpoint, get_endpoint, format_path

logger = logging.getLogger(__name__)


class GausiumAPIClient:
    """
    统一的Gausium API客户端。
    
    消除所有API调用中的重复代码和特殊情况处理。
    """
    
    def __init__(self):
        """初始化API客户端。"""
        self._client: Optional[httpx.AsyncClient] = None
        self._token_manager = TokenManager()
    
    async def __aenter__(self) -> 'GausiumAPIClient':
        """异步上下文管理器入口。"""
        self._client = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口。"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def call_endpoint(
        self,
        endpoint_name: str,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        通过端点名称调用API。
        
        这是主要的API调用方法，使用预定义的端点配置。
        
        Args:
            endpoint_name: 端点名称 (在endpoints.py中定义)
            path_params: 路径参数 (如 {"serial_number": "ABC123"})
            query_params: 查询参数
            json_data: JSON请求体
            
        Returns:
            API响应的JSON数据
            
        Raises:
            KeyError: 端点不存在
            httpx.HTTPStatusError: HTTP错误状态码
            httpx.RequestError: 网络连接错误
            ValueError: 客户端未初始化
        """
        endpoint = get_endpoint(endpoint_name)
        path = format_path(endpoint, **(path_params or {}))
        
        return await self.request(
            method=endpoint.method.value,
            path=path,
            params=query_params,
            json_data=json_data,
            require_auth=endpoint.requires_auth
        )

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        底层API请求方法。
        
        推荐使用 call_endpoint() 方法而不是直接调用此方法。
        
        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            path: API路径 (相对于base URL)
            params: 查询参数
            json_data: JSON请求体
            require_auth: 是否需要认证
            
        Returns:
            API响应的JSON数据
            
        Raises:
            httpx.HTTPStatusError: HTTP错误状态码
            httpx.RequestError: 网络连接错误
            ValueError: 客户端未初始化
        """
        if not self._client:
            raise ValueError("API client not initialized. Use 'async with' context manager.")
        
        # 构建完整URL
        url = urljoin(GAUSIUM_BASE_URL, path.lstrip('/'))
        
        # 准备请求头
        headers = {'Content-Type': 'application/json'}
        if require_auth:
            token = await self._token_manager.get_valid_token()
            headers['Authorization'] = f'Bearer {token}'
        
        # 执行请求
        try:
            logger.debug(f"API request: {method} {url}")
            response = await self._client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise
    
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """GET请求的便捷方法。"""
        return await self.request('GET', path, params=params, require_auth=require_auth)
    
    async def post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """POST请求的便捷方法。"""
        return await self.request('POST', path, params=params, json_data=json_data, require_auth=require_auth)