from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes import router as api_router
from app.core.config import load_settings


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="Funnel API", version="0.1.0")

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix="/api")

    public_dir = Path(__file__).resolve().parents[1] / "public"
    if public_dir.exists():
        app.mount("/static", StaticFiles(directory=public_dir), name="static")

        @app.get("/")
        def ui_index() -> FileResponse:
            return FileResponse(public_dir / "index.html")

        @app.get("/ui")
        def ui_alias() -> FileResponse:
            return FileResponse(public_dir / "index.html")

    return app


app = create_app()
