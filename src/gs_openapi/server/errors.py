"""Unified HTTP error envelopes."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from gs_openapi.core.errors import GausiumAPIError
from gs_openapi.tools.registry import ToolInputError

logger = logging.getLogger(__name__)


def envelope(code: int | str, message: str, trace_id: str | None = None) -> dict:
    return {"error": {"code": code, "message": message, "trace_id": trace_id}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(GausiumAPIError)
    async def upstream_error(request: Request, exc: GausiumAPIError) -> JSONResponse:
        return JSONResponse(envelope(exc.code or 502, exc.msg, exc.trace_id), status_code=502)

    @app.exception_handler(ToolInputError)
    @app.exception_handler(ValidationError)
    @app.exception_handler(RequestValidationError)
    async def input_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(envelope(422, str(exc)), status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(envelope(exc.status_code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled HTTP error on %s %s", request.method, request.url.path,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(envelope(500, "Internal server error"), status_code=500)
