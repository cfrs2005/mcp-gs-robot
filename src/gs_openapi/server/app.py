"""FastAPI application factory."""

import logging
import time

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from gs_openapi import __version__

from .deps import require_api_key
from .errors import register_error_handlers
from .routes import agent, health, robots, tools
from .static import mount_static

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    application = FastAPI(title="GS Robot API", version=__version__)
    application.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
    )

    @application.middleware("http")
    async def log_request(request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            logger.info(
                "%s %s %d %.1fms", request.method, request.url.path,
                status, (time.perf_counter() - start) * 1000,
            )

    register_error_handlers(application)
    public = APIRouter(prefix="/api/v1")
    public.include_router(health.router)
    application.include_router(public)
    protected = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])
    protected.include_router(tools.router)
    protected.include_router(robots.router)
    protected.include_router(agent.router)
    application.include_router(protected)
    mount_static(application)
    return application


app = create_app()
