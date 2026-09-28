"""Built H5 assets and non-API SPA navigation."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent / "static"


def mount_static(app: FastAPI, directory: Path = STATIC_DIR) -> None:
    index = directory / "index.html"
    assets = directory / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    async def home():
        if index.is_file():
            return FileResponse(index)
        return JSONResponse({"message": "H5 not built", "docs": "/docs"})

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Not found")
