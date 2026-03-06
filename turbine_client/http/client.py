"""
HTTP client for Turbine API.
"""

from typing import Any, Dict, List, Optional, Tuple

import httpx

from turbine_client.auth import BearerTokenAuth
from turbine_client.constants import HEADER_CONTENT_TYPE, HEADER_USER_AGENT, USER_AGENT
from turbine_client.exceptions import TurbineApiError


class HttpClient:
    """HTTP client for making requests to the Turbine API."""

    def __init__(
        self,
        host: str,
        auth: Optional[BearerTokenAuth] = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the HTTP client.

        Args:
            host: The API host URL.
            auth: Optional bearer token auth handler.
            timeout: Request timeout in seconds.
        """
        self._host = host.rstrip("/")
        self._auth = auth
        self._timeout = timeout
        self._client = httpx.Client(
            http2=True,
            timeout=timeout,
            headers={
                HEADER_USER_AGENT: USER_AGENT,
                HEADER_CONTENT_TYPE: "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
            },
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "HttpClient":
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        self.close()

    def _build_url(self, endpoint: str) -> str:
        """Build the full URL for an endpoint.

        Args:
            endpoint: The API endpoint path.

        Returns:
            The full URL.
        """
        return f"{self._host}{endpoint}"

    def _get_headers(self, authenticated: bool = False) -> Dict[str, str]:
        """Get request headers.

        Args:
            authenticated: Whether to include auth headers.

        Returns:
            The request headers.
        """
        headers: Dict[str, str] = {}
        if authenticated and self._auth:
            headers.update(self._auth.get_auth_header())
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle an HTTP response.

        Args:
            response: The HTTP response.

        Returns:
            The parsed response data.

        Raises:
            TurbineApiError: If the request failed.
        """
        if response.status_code >= 400:
            try:
                error_body = response.json()
                error_message = error_body.get("error", error_body.get("message", str(error_body)))
            except Exception:
                error_message = response.text or f"HTTP {response.status_code}"

            raise TurbineApiError(
                message=error_message,
                status_code=response.status_code,
                response_body=error_body if "error_body" in dir() else response.text,
            )

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except Exception:
            return response.text

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        authenticated: bool = False,
    ) -> Any:
        """Make a GET request.

        Args:
            endpoint: The API endpoint.
            params: Optional query parameters.
            authenticated: Whether to include auth headers.

        Returns:
            The response data.
        """
        url = self._build_url(endpoint)
        headers = self._get_headers(authenticated)

        try:
            response = self._client.get(url, params=params, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise TurbineApiError(f"Request failed: {e}") from e

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        authenticated: bool = False,
    ) -> Any:
        """Make a POST request.

        Args:
            endpoint: The API endpoint.
            data: The request body.
            authenticated: Whether to include auth headers.

        Returns:
            The response data.
        """
        url = self._build_url(endpoint)
        headers = self._get_headers(authenticated)

        try:
            response = self._client.post(url, json=data, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise TurbineApiError(f"Request failed: {e}") from e

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        authenticated: bool = False,
    ) -> Any:
        """Make a DELETE request.

        Args:
            endpoint: The API endpoint.
            params: Optional query parameters.
            authenticated: Whether to include auth headers.

        Returns:
            The response data.
        """
        url = self._build_url(endpoint)
        headers = self._get_headers(authenticated)

        try:
            response = self._client.delete(url, params=params, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise TurbineApiError(f"Request failed: {e}") from e

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        authenticated: bool = False,
    ) -> Any:
        """Make a PUT request.

        Args:
            endpoint: The API endpoint.
            data: The request body.
            authenticated: Whether to include auth headers.

        Returns:
            The response data.
        """
        url = self._build_url(endpoint)
        headers = self._get_headers(authenticated)

        try:
            response = self._client.put(url, json=data, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise TurbineApiError(f"Request failed: {e}") from e
