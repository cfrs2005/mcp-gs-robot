"""
Error types for Gausium OpenAPI V3.

These exception classes provide structured information about API failures,
including the business status code, message, trace ID, HTTP status, and the
endpoint that was called.
"""



class GausiumError(Exception):
    """Base exception for all Gausium OpenAPI errors."""


class GausiumAuthError(GausiumError):
    """Raised when authentication fails (token acquisition or refresh)."""

    def __init__(self, message: str, *, trace_id: str | None = None) -> None:
        super().__init__(message)
        self.trace_id = trace_id


class GausiumAPIError(GausiumError):
    """
    Raised when a V3 business endpoint returns a non-zero ``code`` in the
    response envelope, or when an HTTP error occurs that is not retried.

    Attributes:
        code: Business status code from the envelope (``code`` field). 0 means
            success; non-zero values are six-digit error codes. May be ``None``
            for pure HTTP transport errors.
        msg: Human-readable message from the envelope ``msg`` field.
        trace_id: Request trace ID (``traceId``) when available.
        http_status: HTTP status code of the response.
        endpoint: The V3 endpoint name that was called.
    """

    def __init__(
        self,
        msg: str,
        *,
        code: int | None = None,
        trace_id: str | None = None,
        http_status: int | None = None,
        endpoint: str | None = None,
    ) -> None:
        super().__init__(msg)
        self.msg = msg
        self.code = code
        self.trace_id = trace_id
        self.http_status = http_status
        self.endpoint = endpoint

    def __str__(self) -> str:
        parts = [f"GausiumAPIError: {self.msg}"]
        if self.code is not None:
            parts.append(f"code={self.code}")
        if self.http_status is not None:
            parts.append(f"http_status={self.http_status}")
        if self.trace_id:
            parts.append(f"traceId={self.trace_id}")
        if self.endpoint:
            parts.append(f"endpoint={self.endpoint}")
        return " ".join(parts)
