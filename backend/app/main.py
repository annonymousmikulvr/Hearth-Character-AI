"""
Local Character AI – FastAPI application entry point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_runtime_config, settings
from app.schema_ensure import ensure_columns
from app.database import close_database, open_database, run_migrations
from app.routes import api_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("local_character_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: if a runtime config already exists, open the DB and apply migrations
    cfg = load_runtime_config()
    if cfg is not None:
        try:
            db = await open_database(cfg.database_path)
            migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
            await run_migrations(db, migrations_dir)
            await ensure_columns(db)
            logger.info("Database ready at %s", cfg.database_path)
        except Exception as exc:
            logger.warning("Could not open existing database: %s", exc)
    yield
    await close_database()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Local-only CORS – the React app and Tauri webview both talk to 127.0.0.1
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8741",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/api/docs",
    }
