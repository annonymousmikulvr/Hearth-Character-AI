from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import aiosqlite

from app.database import get_db_dependency
from app.schemas.persona import (
    PersonaCreate,
    PersonaUpdate,
    PersonaOut,
    PersonaListItem,
)
from app.schemas.common import MessageResponse
from app.services.persona_service import PersonaService
from app.services.settings_service import SettingsService

router = APIRouter()


def _to_out(p) -> PersonaOut:
    return PersonaOut(
        id=p.id,
        profile_name=p.profile_name,
        chat_name=p.chat_name,
        age=p.age,
        pronouns=p.pronouns,
        height=p.height,
        build=p.build,
        hair=p.hair,
        eyes=p.eyes,
        skin=p.skin,
        clothing=p.clothing,
        appearance_description=p.appearance_description,
        traits=p.traits,
        personality_description=p.personality_description,
        likes=p.likes,
        dislikes=p.dislikes,
        habits=p.habits,
        speaking_style=p.speaking_style,
        biography=p.biography,
        occupation=p.occupation,
        location=p.location,
        additional_facts=p.additional_facts,
        how_they_act=p.how_they_act,
        how_they_respond=p.how_they_respond,
        custom_instructions=p.custom_instructions,
        example_dialogues=p.example_dialogues,
        family_tree=getattr(p, 'family_tree', None) or [],
        relationships=getattr(p, 'relationships', None) or [],
        tags=p.tags,
        avatar_path=p.avatar_path,
        is_archived=p.is_archived,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=list[PersonaListItem])
async def list_personas(
    include_archived: bool = False,
    search: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = PersonaService(db)
    personas = await svc.list(
        include_archived=include_archived,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [
        PersonaListItem(
            id=p.id,
            profile_name=p.profile_name,
            chat_name=p.chat_name,
            avatar_path=p.avatar_path,
            tags=p.tags,
            is_archived=p.is_archived,
            updated_at=p.updated_at,
        )
        for p in personas
    ]


@router.post("", response_model=PersonaOut, status_code=201)
async def create_persona(
    body: PersonaCreate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = PersonaService(db)
    persona = await svc.create(body)
    return _to_out(persona)


@router.get("/{persona_id}", response_model=PersonaOut)
async def get_persona(
    persona_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = PersonaService(db)
    persona = await svc.get(persona_id)
    if persona is None:
        raise HTTPException(404, "Persona not found")
    return _to_out(persona)


@router.patch("/{persona_id}", response_model=PersonaOut)
async def update_persona(
    persona_id: str,
    body: PersonaUpdate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = PersonaService(db)
    persona = await svc.update(persona_id, body)
    if persona is None:
        raise HTTPException(404, "Persona not found")
    return _to_out(persona)


@router.delete("/{persona_id}", response_model=MessageResponse)
async def delete_persona(
    persona_id: str,
    hard: bool = False,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    # If this is the default persona, clear the default
    settings_svc = SettingsService(db)
    default_id = await settings_svc.get_default_persona_id()
    if default_id == persona_id:
        await settings_svc.set_default_persona_id(None)

    svc = PersonaService(db)
    ok = await svc.delete(persona_id, hard=hard)
    if not ok:
        raise HTTPException(404, "Persona not found")
    return MessageResponse(message="Persona deleted" if hard else "Persona archived")


from fastapi.responses import Response
from fastapi import File, UploadFile
from app.services.export_service import export_persona_zip, import_persona_from_zip
from app.schemas.persona import PersonaCreate


@router.get("/{persona_id}/export")
async def export_persona(
    persona_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = PersonaService(db)
    persona = await svc.get(persona_id)
    if persona is None:
        raise HTTPException(404, "Persona not found")
    data = export_persona_zip(persona)
    filename = f"{persona.profile_name.replace(' ', '_')}.persona"
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=PersonaOut, status_code=201)
async def import_persona(
    file: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    raw = await file.read()
    if len(raw) > 5_000_000:
        raise HTTPException(400, "Package too large")
    try:
        obj = import_persona_from_zip(raw)
    except Exception as e:
        raise HTTPException(400, f"Invalid package: {e}")
    payload = PersonaCreate(
        profile_name=obj["profile_name"],
        chat_name=obj.get("chat_name") or obj["profile_name"],
        age=obj.get("age"),
        pronouns=obj.get("pronouns"),
        height=obj.get("height"),
        build=obj.get("build"),
        hair=obj.get("hair"),
        eyes=obj.get("eyes"),
        skin=obj.get("skin"),
        clothing=obj.get("clothing"),
        appearance_description=obj.get("appearance_description"),
        traits=obj.get("traits") or [],
        personality_description=obj.get("personality_description"),
        likes=obj.get("likes") or [],
        dislikes=obj.get("dislikes") or [],
        habits=obj.get("habits") or [],
        speaking_style=obj.get("speaking_style"),
        biography=obj.get("biography"),
        occupation=obj.get("occupation"),
        location=obj.get("location"),
        additional_facts=obj.get("additional_facts") or [],
        how_they_act=obj.get("how_they_act"),
        how_they_respond=obj.get("how_they_respond"),
        custom_instructions=obj.get("custom_instructions"),
        example_dialogues=obj.get("example_dialogues") or [],
        tags=obj.get("tags") or [],
    )
    svc = PersonaService(db)
    persona = await svc.create(payload)
    return _to_out(persona)
