"""
Custom exceptions for the Turbine Python client.
"""

from typing import Any, Optional


class TurbineError(Exception):
    """Base exception for Turbine client errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class TurbineApiError(TurbineError):
    """Exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Any = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

    def __str__(self) -> str:
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}"
        return f"API Error: {self.message}"


class OrderValidationError(TurbineError):
    """Exception for order validation errors."""

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        self.field = field
        super().__init__(message)

    def __str__(self) -> str:
        if self.field:
            return f"Order Validation Error ({self.field}): {self.message}"
        return f"Order Validation Error: {self.message}"


class SignatureError(TurbineError):
    """Exception for signature-related errors."""

    pass


class AuthenticationError(TurbineError):
    """Exception for authentication errors."""

    def __init__(self, message: str, required_level: Optional[str] = None) -> None:
        self.required_level = required_level
        super().__init__(message)

    def __str__(self) -> str:
        if self.required_level:
            return f"Authentication Error (requires {self.required_level}): {self.message}"
        return f"Authentication Error: {self.message}"


class ConfigurationError(TurbineError):
    """Exception for configuration errors."""

    pass


class WebSocketError(TurbineError):
    """Exception for WebSocket errors."""

    pass
