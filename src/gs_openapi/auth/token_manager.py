"""
Token management module for Gausium OpenAPI authentication.

Provides token lifecycle management: acquisition, storage, and renewal of
OAuth tokens. V3 notes:

* The auth endpoints keep the legacy URL ``/gas/api/v1alpha1/oauth/token``.
* The token response field ``expires_in`` is a UTC timestamp in *milliseconds*
  (e.g. 1726111975164), **not** a duration. This module interprets it
  defensively:
    - ``> 1e11``  → milliseconds epoch (divide by 1000)
    - ``> 1e9``   → seconds epoch (use directly)
    - otherwise   → duration in seconds from now
* Refresh is protected by an :class:`asyncio.Lock` and uses a 5-minute buffer.
* ``print`` is replaced with ``logging``.
* Credentials and an :class:`httpx.AsyncClient` may be injected via the
  constructor (for tests); defaults still read the ``GS_*`` env vars.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from urllib.parse import urljoin

import httpx

from ..config import (
    ENV_VAR_CLIENT_ID,
    ENV_VAR_CLIENT_SECRET,
    ENV_VAR_OPEN_ACCESS_KEY,
    GAUSIUM_BASE_URL,
    TOKEN_PATH,
)
from ..core.errors import GausiumAuthError

logger = logging.getLogger(__name__)

# Heuristics for interpreting the ``expires_in`` field.
_MS_EPOCH_THRESHOLD = 1e11      # values above this are milliseconds-epoch
_SEC_EPOCH_THRESHOLD = 1e9      # values above this are seconds-epoch


def _compute_expires_at(expires_in: float) -> float:
    """
    Convert the ``expires_in`` value returned by the OAuth endpoint into an
    absolute expiry timestamp (seconds since the epoch).

    The V3 docs state ``expires_in`` is a UTC timestamp in milliseconds. To
    remain robust against older responses that returned a duration, we detect
    the magnitude of the value.
    """
    if expires_in > _MS_EPOCH_THRESHOLD:
        # Milliseconds epoch → seconds epoch.
        return expires_in / 1000.0
    if expires_in > _SEC_EPOCH_THRESHOLD:
        # Seconds epoch.
        return float(expires_in)
    # Duration in seconds from now.
    return time.time() + float(expires_in)


class TokenManager:
    """Manages OAuth token lifecycle for the Gausium API."""

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        open_access_key: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
    ) -> None:
        """
        Initialize the TokenManager.

        Args:
            client_id: Application client ID. Defaults to ``GS_CLIENT_ID``.
            client_secret: Application client secret. Defaults to
                ``GS_CLIENT_SECRET``.
            open_access_key: Communication key (AccessKeySecret). Defaults to
                ``GS_OPEN_ACCESS_KEY``.
            http_client: Optional injected :class:`httpx.AsyncClient`. When
                provided it is used for token requests and is **not** closed by
                this manager. When omitted, a transient client is created per
                request (legacy behaviour).
            base_url: Override for the API base URL. Defaults to
                :data:`GAUSIUM_BASE_URL`.
        """
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        # Buffer time (in seconds) before actual expiration to refresh token.
        self._refresh_buffer: int = 300  # 5 minutes

        self._client_id = client_id or os.getenv(ENV_VAR_CLIENT_ID)
        self._client_secret = client_secret or os.getenv(ENV_VAR_CLIENT_SECRET)
        self._open_access_key = open_access_key or os.getenv(ENV_VAR_OPEN_ACCESS_KEY)
        self._base_url = base_url or GAUSIUM_BASE_URL
        self._http_client = http_client
        self._lock = asyncio.Lock()

        if not all([self._client_id, self._client_secret, self._open_access_key]):
            missing = [
                name
                for name, val in {
                    ENV_VAR_CLIENT_ID: self._client_id,
                    ENV_VAR_CLIENT_SECRET: self._client_secret,
                    ENV_VAR_OPEN_ACCESS_KEY: self._open_access_key,
                }.items()
                if not val
            ]
            raise GausiumAuthError(
                f"Missing required credentials: {', '.join(missing)}. "
                "Set the corresponding GS_* environment variables or pass them "
                "to the TokenManager constructor."
            )

    async def get_valid_token(self) -> str:
        """
        Return a valid access token, refreshing or acquiring as needed.

        Concurrent callers are serialised by an :class:`asyncio.Lock` so that
        the token is refreshed at most once.
        """
        async with self._lock:
            if self._is_token_valid():
                assert self._access_token is not None
                return self._access_token
            if self._refresh_token:
                await self._refresh_access_token()
            else:
                await self._get_new_token()
            assert self._access_token is not None
            return self._access_token

    def invalidate(self) -> None:
        """Invalidate the cached token so the next call acquires/refreshes."""
        self._access_token = None
        self._expires_at = 0.0
        # Keep the refresh token: it may still be reusable.

    def _is_token_valid(self) -> bool:
        """Check if the current token is valid and not near expiration."""
        if not self._access_token:
            return False
        return time.time() < (self._expires_at - self._refresh_buffer)

    async def _request_token(self, payload: dict) -> None:
        """POST to the token endpoint and store the resulting token."""
        url = urljoin(self._base_url, TOKEN_PATH)
        try:
            if self._http_client is not None:
                response = await self._http_client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data["access_token"]
            self._refresh_token = token_data.get("refresh_token", self._refresh_token)
            self._expires_at = _compute_expires_at(float(token_data["expires_in"]))
        except httpx.HTTPError as e:
            logger.error("Token request failed: %s", e)
            raise GausiumAuthError(f"Token request failed: {e}") from e
        except KeyError as e:
            logger.error("Token response missing field: %s", e)
            raise GausiumAuthError(f"Token response missing field: {e}") from e

    async def _get_new_token(self) -> None:
        """Acquire a brand-new access token using application credentials."""
        logger.debug("Acquiring new OAuth token")
        payload = {
            "grant_type": "urn:gaussian:params:oauth:grant-type:open-access-token",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "open_access_key": self._open_access_key,
        }
        await self._request_token(payload)

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        logger.debug("Refreshing OAuth token")
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }
        try:
            await self._request_token(payload)
        except GausiumAuthError:
            # Refresh failed; clear tokens to force fresh acquisition next time.
            self._access_token = None
            self._refresh_token = None
            raise
