"""
Application configuration.
Only the selected database path and a few runtime flags live outside the SQLite DB.
Everything else (AI config, playback, default persona, etc.) is stored in the database.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class RuntimeConfig(BaseModel):
    """Lightweight config stored next to the chosen data root."""

    data_root: Path
    database_path: Path
    version: str = "0.2.0"


class Settings(BaseSettings):
    """Process-level settings. Overridable via environment variables."""

    app_name: str = "Local Character AI"
    app_version: str = "0.2.0"
    host: str = "127.0.0.1"
    port: int = 8741
    debug: bool = False

    # Default Ollama endpoint – never leave the local machine by default
    ollama_base_url: str = "http://127.0.0.1:11434"

    # Where the lightweight runtime config lives when no data root is chosen yet
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".local-character-ai")

    class Config:
        env_prefix = "LCAI_"
        env_file = ".env"


settings = Settings()


def get_runtime_config_path() -> Path:
    return settings.config_dir / "runtime.json"


def load_runtime_config() -> Optional[RuntimeConfig]:
    path = get_runtime_config_path()
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return RuntimeConfig(
        data_root=Path(data["data_root"]),
        database_path=Path(data["database_path"]),
        version=data.get("version", "0.2.0"),
    )


def save_runtime_config(cfg: RuntimeConfig) -> None:
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    path = get_runtime_config_path()
    path.write_text(
        json.dumps(
            {
                "data_root": str(cfg.data_root),
                "database_path": str(cfg.database_path),
                "version": cfg.version,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def clear_runtime_config() -> None:
    path = get_runtime_config_path()
    if path.exists():
        path.unlink()
