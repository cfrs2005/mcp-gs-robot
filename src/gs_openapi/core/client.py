"""
统一的Gausium API客户端实现。

这个模块实现Linus原则：
1. 消除特殊情况 - 所有API调用使用统一方法
2. 好品味的设计 - 单一职责，明确边界
3. 简洁性 - 不超过3层缩进
"""

from __future__ import annotations

import logging
from typing import Any, Self
from urllib.parse import urljoin

import httpx

from ..auth.token_manager import TokenManager
from ..config import GAUSIUM_BASE_URL, GS_HTTP_TIMEOUT
from .endpoints import format_path, get_endpoint
from .errors import GausiumAPIError

logger = logging.getLogger(__name__)


class GausiumAPIClient:
    """
    统一的Gausium API客户端。

    消除所有API调用中的重复代码和特殊情况处理。V3 业务端点通过
    :meth:`call_v3` 调用，统一处理响应信封和 401 重试。
    """

    def __init__(
        self,
        *,
        token_manager: TokenManager | None = None,
        http_client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        """
        Initialize the API client.

        Args:
            token_manager: Optional injected :class:`TokenManager`. When
                omitted, a default one is created (reads ``GS_*`` env vars).
            http_client: Optional injected :class:`httpx.AsyncClient`. When
                omitted, one is created lazily with the configured timeout.
            base_url: Override for the API base URL.
            timeout: HTTP timeout in seconds (defaults to ``GS_HTTP_TIMEOUT``).
        """
        self._base_url = base_url or GAUSIUM_BASE_URL
        self._timeout = timeout if timeout is not None else GS_HTTP_TIMEOUT
        self._token_manager = token_manager  # may be None until needed
        self._owns_http_client = http_client is None
        self._client: httpx.AsyncClient | None = http_client
        # Default token manager is created lazily so that constructing the
        # client does not require credentials when an injected manager is used.
        if token_manager is None:
            self._token_manager = TokenManager()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily create the shared httpx client if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
            self._owns_http_client = True
        return self._client

    async def __aenter__(self) -> Self:
        """异步上下文管理器入口。"""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口。"""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the shared HTTP client if this instance owns it."""
        if self._client is not None and self._owns_http_client:
            await self._client.aclose()
            self._client = None

    async def call_endpoint(
        self,
        endpoint_name: str,
        path_params: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        通过端点名称调用API (legacy behaviour, unchanged).
        """
        endpoint = get_endpoint(endpoint_name)
        path = format_path(endpoint, **(path_params or {}))

        return await self.request(
            method=endpoint.method.value,
            path=path,
            params=query_params,
            json_data=json_data,
            require_auth=endpoint.requires_auth,
        )

    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        """
        底层API请求方法 (legacy behaviour, unchanged).
        """
        client = await self._ensure_client()

        url = urljoin(self._base_url, path.lstrip("/"))

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if require_auth:
            token = await self._token_manager.get_valid_token()
            headers["Authorization"] = f"Bearer {token}"

        try:
            logger.debug("API request: %s %s", method, url)
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error("API error %d: %s", e.response.status_code, e.response.text)
            raise
        except httpx.RequestError as e:
            logger.error("Network error: %s", e)
            raise

    async def call_v3(self, endpoint_name: str, json_data: dict) -> Any:
        """
        Call a V3 business endpoint and unwrap the response envelope.

        Resolves the endpoint by name (e.g. ``v3_robots_status_get``), POSTs
        the JSON body with a Bearer token, and returns the unwrapped
        ``data`` payload. On a non-zero business ``code`` or an HTTP error, a
        :class:`GausiumAPIError` is raised. On HTTP 401 the cached token is
        invalidated and the request is retried exactly once.

        Args:
            endpoint_name: A key in :data:`V3_ENDPOINTS` (``v3_...``).
            json_data: The JSON request body.

        Returns:
            The ``data`` field of the response envelope (type depends on the
            endpoint; typically a dict, list, or empty object).

        Raises:
            GausiumAPIError: On non-zero business code or HTTP error.
            KeyError: If ``endpoint_name`` is not a registered V3 endpoint.
        """
        endpoint = get_endpoint(endpoint_name)
        path = format_path(endpoint)
        url = urljoin(self._base_url, path.lstrip("/"))
        client = await self._ensure_client()

        return await self._call_v3_once(client, url, endpoint_name, json_data, retried=False)

    async def _call_v3_once(
        self,
        client: httpx.AsyncClient,
        url: str,
        endpoint_name: str,
        json_data: dict,
        *,
        retried: bool,
    ) -> Any:
        token = await self._token_manager.get_valid_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        logger.debug("V3 request: POST %s", url)
        try:
            response = await client.post(url, json=json_data, headers=headers)
        except httpx.RequestError as e:
            logger.error("V3 network error on %s: %s", endpoint_name, e)
            raise GausiumAPIError(
                f"Network error: {e}", http_status=None, endpoint=endpoint_name
            ) from e

        # Handle HTTP 401: invalidate token and retry exactly once.
        if response.status_code == 401 and not retried:
            logger.warning(
                "V3 endpoint %s returned 401; invalidating token and retrying once",
                endpoint_name,
            )
            self._token_manager.invalidate()
            return await self._call_v3_once(
                client, url, endpoint_name, json_data, retried=True
            )

        # Non-2xx HTTP status (other than the 401 already handled).
        if not (200 <= response.status_code < 300):
            self._raise_from_response(response, endpoint_name, envelope=False)

        # Parse the unified envelope {code, msg, traceId, data}.
        try:
            body = response.json()
        except ValueError as e:
            raise GausiumAPIError(
                f"Invalid JSON response: {e}",
                http_status=response.status_code,
                endpoint=endpoint_name,
            ) from e

        code = body.get("code")
        if code != 0:
            raise GausiumAPIError(
                body.get("msg", "unknown error"),
                code=code if isinstance(code, int) else None,
                trace_id=body.get("traceId"),
                http_status=response.status_code,
                endpoint=endpoint_name,
            )

        return body.get("data")

    @staticmethod
    def _raise_from_response(
        response: httpx.Response, endpoint_name: str, *, envelope: bool
    ) -> None:
        trace_id: str | None = None
        msg = response.text
        try:
            body = response.json()
            if isinstance(body, dict):
                trace_id = body.get("traceId")
                msg = body.get("msg", msg)
        except ValueError:
            pass
        raise GausiumAPIError(
            msg,
            code=None,
            trace_id=trace_id,
            http_status=response.status_code,
            endpoint=endpoint_name,
        )

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        """GET请求的便捷方法。"""
        return await self.request("GET", path, params=params, require_auth=require_auth)

    async def post(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        """POST请求的便捷方法。"""
        return await self.request(
            "POST", path, params=params, json_data=json_data, require_auth=require_auth
        )
