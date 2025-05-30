"""
Token management module for Gausium OpenAPI authentication.

This module provides token lifecycle management including acquisition,
storage, and renewal of OAuth tokens.
"""

import os
import time
from typing import Optional
import httpx
from urllib.parse import urljoin

from ..config import (
    GAUSIUM_BASE_URL,
    TOKEN_PATH,
    ENV_VAR_CLIENT_ID,
    ENV_VAR_CLIENT_SECRET,
    ENV_VAR_OPEN_ACCESS_KEY
)

class TokenManager:
    """Manages OAuth token lifecycle for Gausium API.
    
    This class handles token acquisition, storage, and renewal, implementing
    a centralized token management strategy as per python.mdc Sec 3.1 optimization
    techniques (caching) and Sec 4.3 authentication patterns.
    """
    
    def __init__(self):
        """Initialize the TokenManager."""
        self._access_token: Optional[str] = None
        self._expires_at: float = 0
        # Buffer time (in seconds) before actual expiration to refresh token
        self._refresh_buffer: int = 300  # 5 minutes
        
        # Validate and store credentials
        self._client_id = os.getenv(ENV_VAR_CLIENT_ID)
        self._client_secret = os.getenv(ENV_VAR_CLIENT_SECRET)
        self._open_access_key = os.getenv(ENV_VAR_OPEN_ACCESS_KEY)
        
        if not all([self._client_id, self._client_secret, self._open_access_key]):
            missing_vars = [
                var for var, val in {
                    ENV_VAR_CLIENT_ID: self._client_id,
                    ENV_VAR_CLIENT_SECRET: self._client_secret,
                    ENV_VAR_OPEN_ACCESS_KEY: self._open_access_key
                }.items() if not val
            ]
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary.
        
        Returns:
            str: A valid access token.
            
        Raises:
            httpx.HTTPStatusError: If token refresh fails due to API error
            httpx.RequestError: If there are network connectivity issues
        """
        if not self._is_token_valid():
            await self._refresh_token()
        return self._access_token
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is valid and not near expiration."""
        if not self._access_token:
            return False
        # Consider token invalid if it's within refresh buffer of expiration
        return time.time() < (self._expires_at - self._refresh_buffer)
    
    async def _refresh_token(self) -> None:
        """Refresh the access token.
        
        Raises:
            httpx.HTTPStatusError: If the API returns an error response
            httpx.RequestError: If there are network connectivity issues
            KeyError: If the API response is missing expected fields
        """
        # Construct full URL using urljoin
        full_token_url = urljoin(GAUSIUM_BASE_URL, TOKEN_PATH)
        
        async with httpx.AsyncClient() as client:
            try:
                token_payload = {
                    "grant_type": "urn:gaussian:params:oauth:grant-type:open-access-token",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "open_access_key": self._open_access_key
                }
                response = await client.post(
                    full_token_url,
                    json=token_payload,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                token_data = response.json()
                
                self._access_token = token_data['access_token']
                # Convert expires_in to absolute timestamp
                self._expires_at = time.time() + float(token_data['expires_in'])
                
            except (httpx.HTTPStatusError, KeyError) as e:
                print(f"Error refreshing token: {str(e)}")
                raise
