"""Start the HTTP server from the installed command or python -m."""

import argparse
import os

import uvicorn

from ..config import load_env


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the GS Robot HTTP server")
    parser.add_argument("--reload", action="store_true", help="Reload on code changes")
    args = parser.parse_args()
    load_env()  # GS_SERVER_HOST / GS_SERVER_PORT may come from .env
    uvicorn.run(
        "gs_openapi.server.app:app",
        host=os.getenv("GS_SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("GS_SERVER_PORT", "8000")),
        log_level="info",
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
