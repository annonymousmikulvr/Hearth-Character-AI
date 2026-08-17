from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_db_dependency
from app.services.settings_service import SettingsService
from app.services.persona_service import PersonaService
import aiosqlite

router = APIRouter()


class SettingUpdate(BaseModel):
    value: str


class DefaultPersonaUpdate(BaseModel):
    persona_id: Optional[str] = None


@router.get("")
async def get_all_settings(db: aiosqlite.Connection = Depends(get_db_dependency)):
    svc = SettingsService(db)
    return await svc.get_all()


# Static paths must be registered before the {key} catch-all
@router.get("/default-persona/current")
async def get_default_persona(db: aiosqlite.Connection = Depends(get_db_dependency)):
    svc = SettingsService(db)
    persona_id = await svc.get_default_persona_id()
    if not persona_id:
        return {"persona_id": None, "persona": None}
    persona_svc = PersonaService(db)
    persona = await persona_svc.get(persona_id)
    return {
        "persona_id": persona_id,
        "persona": persona,
    }


@router.put("/default-persona")
async def set_default_persona(
    body: DefaultPersonaUpdate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = SettingsService(db)
    if body.persona_id:
        persona_svc = PersonaService(db)
        persona = await persona_svc.get(body.persona_id)
        if persona is None:
            raise HTTPException(404, "Persona not found")
        if persona.is_archived:
            raise HTTPException(400, "Cannot set an archived persona as default")
    await svc.set_default_persona_id(body.persona_id)
    return {"persona_id": body.persona_id}


@router.get("/{key}")
async def get_setting(key: str, db: aiosqlite.Connection = Depends(get_db_dependency)):
    svc = SettingsService(db)
    val = await svc.get(key)
    if val is None:
        raise HTTPException(404, f"Setting '{key}' not found")
    return {"key": key, "value": val}


@router.put("/{key}")
async def put_setting(
    key: str,
    body: SettingUpdate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = SettingsService(db)
    await svc.set(key, body.value)
    return {"key": key, "value": body.value}
