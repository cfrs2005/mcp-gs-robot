"""FastAPI entry point for the V3 HTTP server."""

from .app import create_app

__all__ = ["create_app"]
