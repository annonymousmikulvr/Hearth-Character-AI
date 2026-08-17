from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import (
    RuntimeConfig,
    load_runtime_config,
    save_runtime_config,
    settings,
)
from app.schema_ensure import ensure_columns
from app.database import (
    close_database,
    ensure_data_directories,
    open_database,
    run_migrations,
)
from app.services.settings_service import SettingsService

router = APIRouter()


class SetupRequest(BaseModel):
    data_root: str = Field(..., description="Absolute path chosen by the user")
    create_new: bool = True


class SetupStatus(BaseModel):
    setup_completed: bool
    data_root: Optional[str] = None
    database_path: Optional[str] = None
    version: str = settings.app_version


@router.get("", response_model=SetupStatus)
async def get_setup_status():
    cfg = load_runtime_config()
    if cfg is None:
        return SetupStatus(setup_completed=False)

    # Check whether the DB thinks setup is finished
    try:
        db = await open_database(cfg.database_path)
        svc = SettingsService(db)
        completed = await svc.get_bool("setup_completed", False)
        return SetupStatus(
            setup_completed=completed,
            data_root=str(cfg.data_root),
            database_path=str(cfg.database_path),
        )
    except Exception:
        return SetupStatus(setup_completed=False)


@router.post("", response_model=SetupStatus)
async def perform_setup(body: SetupRequest):
    data_root = Path(body.data_root).expanduser().resolve()
    if not data_root.is_absolute():
        raise HTTPException(400, "data_root must be an absolute path")

    db_path = data_root / "database.db"

    if body.create_new and db_path.exists():
        # Allow overwrite only if the caller explicitly wants a new DB;
        # for safety we still refuse if the file already exists and looks non-empty.
        # Caller can force by deleting first.
        raise HTTPException(
            409,
            f"Database already exists at {db_path}. "
            "Choose a different location or open the existing database.",
        )

    await ensure_data_directories(data_root)
    db = await open_database(db_path)

    migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
    await run_migrations(db, migrations_dir)
    await ensure_columns(db)

    svc = SettingsService(db)
    await svc.set_bool("setup_completed", True)

    cfg = RuntimeConfig(
        data_root=data_root,
        database_path=db_path,
        version=settings.app_version,
    )
    save_runtime_config(cfg)

    return SetupStatus(
        setup_completed=True,
        data_root=str(data_root),
        database_path=str(db_path),
    )


@router.post("/open")
async def open_existing(body: SetupRequest):
    """Open an already-created database without wiping it."""
    data_root = Path(body.data_root).expanduser().resolve()
    db_path = data_root / "database.db"
    if not db_path.exists():
        raise HTTPException(404, f"No database found at {db_path}")

    await close_database()
    db = await open_database(db_path)
    migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
    await run_migrations(db, migrations_dir)
    await ensure_columns(db)

    cfg = RuntimeConfig(
        data_root=data_root,
        database_path=db_path,
        version=settings.app_version,
    )
    save_runtime_config(cfg)

    svc = SettingsService(db)
    await svc.set_bool("setup_completed", True)

    return SetupStatus(
        setup_completed=True,
        data_root=str(data_root),
        database_path=str(db_path),
    )
