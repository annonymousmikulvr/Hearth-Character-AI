from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import aiosqlite

from app.database import get_db_dependency
from app.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    CharacterOut,
    CharacterListItem,
)
from app.schemas.common import MessageResponse
from app.services.character_service import CharacterService

router = APIRouter()


def _to_out(c) -> CharacterOut:
    return CharacterOut(
        id=c.id,
        name=c.name,
        description=c.description,
        filter_level=getattr(c, "filter_level", None) or "mature",
        system_prompt=c.system_prompt,
        baseline_personality=c.baseline_personality,
        scenario=c.scenario,
        greeting=c.greeting,
        example_dialogues=c.example_dialogues,
        age=getattr(c, "age", None),
        pronouns=getattr(c, "pronouns", None),
        height=getattr(c, "height", None),
        build=getattr(c, "build", None),
        hair=getattr(c, "hair", None),
        eyes=getattr(c, "eyes", None),
        skin=getattr(c, "skin", None),
        clothing=getattr(c, "clothing", None),
        appearance_description=getattr(c, "appearance_description", None),
        traits=getattr(c, "traits", None) or [],
        likes=getattr(c, "likes", None) or [],
        dislikes=getattr(c, "dislikes", None) or [],
        habits=getattr(c, "habits", None) or [],
        speaking_style=getattr(c, "speaking_style", None),
        occupation=getattr(c, "occupation", None),
        location=getattr(c, "location", None),
        biography=getattr(c, "biography", None),
        additional_facts=getattr(c, "additional_facts", None) or [],
        how_they_act=getattr(c, "how_they_act", None),
        how_they_respond=getattr(c, "how_they_respond", None),
        custom_instructions=getattr(c, "custom_instructions", None),
        family_tree=getattr(c, "family_tree", None) or [],
        relationships=getattr(c, "relationships", None) or [],
        goals=getattr(c, "goals", None),
        fears=getattr(c, "fears", None),
        secrets=getattr(c, "secrets", None),
        temperature=c.temperature,
        top_p=c.top_p,
        repetition_penalty=c.repetition_penalty,
        context_window=c.context_window,
        max_tokens=c.max_tokens,
        model_profile_id=c.model_profile_id,
        model_name=c.model_name,
        side_character_enabled=c.side_character_enabled,
        side_character_instructions=c.side_character_instructions,
        image_gen_enabled=getattr(c, "image_gen_enabled", False),
        image_gen_style=getattr(c, "image_gen_style", None),
        side_roster=getattr(c, "side_roster", None) or [],
        mood_board=getattr(c, "mood_board", None) or [],
        trigger_phrases=getattr(c, "trigger_phrases", None) or [],
        tags=c.tags,
        avatar_path=c.avatar_path,
        version=c.version,
        is_archived=c.is_archived,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[CharacterListItem])
async def list_characters(
    include_archived: bool = False,
    search: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = CharacterService(db)
    characters = await svc.list(
        include_archived=include_archived,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [
        CharacterListItem(
            id=c.id,
            name=c.name,
            description=c.description,
            avatar_path=c.avatar_path,
            filter_level=getattr(c, "filter_level", None) or "mature",
            tags=c.tags,
            is_archived=c.is_archived,
            updated_at=c.updated_at,
        )
        for c in characters
    ]


@router.post("", response_model=CharacterOut, status_code=201)
async def create_character(
    body: CharacterCreate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = CharacterService(db)
    character = await svc.create(body)
    return _to_out(character)


@router.get("/{character_id}", response_model=CharacterOut)
async def get_character(
    character_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = CharacterService(db)
    character = await svc.get(character_id)
    if character is None:
        raise HTTPException(404, "Character not found")
    return _to_out(character)


@router.patch("/{character_id}", response_model=CharacterOut)
async def update_character(
    character_id: str,
    body: CharacterUpdate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = CharacterService(db)
    character = await svc.update(character_id, body)
    if character is None:
        raise HTTPException(404, "Character not found")
    return _to_out(character)


@router.delete("/{character_id}", response_model=MessageResponse)
async def delete_character(
    character_id: str,
    hard: bool = False,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = CharacterService(db)
    ok = await svc.delete(character_id, hard=hard)
    if not ok:
        raise HTTPException(404, "Character not found")
    return MessageResponse(message="Character deleted" if hard else "Character archived")


from fastapi.responses import Response
from app.services.export_service import export_character_zip, import_character_from_zip
from app.schemas.character import CharacterCreate
from fastapi import File, UploadFile


@router.get("/{character_id}/export")
async def export_character(
    character_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = CharacterService(db)
    character = await svc.get(character_id)
    if character is None:
        raise HTTPException(404, "Character not found")
    data = export_character_zip(character)
    filename = f"{character.name.replace(' ', '_')}.char"
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=CharacterOut, status_code=201)
async def import_character(
    file: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    raw = await file.read()
    if len(raw) > 5_000_000:
        raise HTTPException(400, "Package too large")
    try:
        obj = import_character_from_zip(raw)
    except Exception as e:
        raise HTTPException(400, f"Invalid package: {e}")
    payload = CharacterCreate(
        name=obj["name"],
        description=obj.get("description"),
        system_prompt=obj.get("system_prompt"),
        baseline_personality=obj.get("baseline_personality"),
        scenario=obj.get("scenario"),
        greeting=obj.get("greeting"),
        example_dialogues=obj.get("example_dialogues") or [],
        temperature=obj.get("temperature"),
        top_p=obj.get("top_p"),
        repetition_penalty=obj.get("repetition_penalty"),
        context_window=obj.get("context_window"),
        max_tokens=obj.get("max_tokens"),
        model_name=obj.get("model_name"),
        side_character_enabled=obj.get("side_character_enabled", True),
        side_character_instructions=obj.get("side_character_instructions"),
        tags=obj.get("tags") or [],
    )
    svc = CharacterService(db)
    character = await svc.create(payload)
    return _to_out(character)


@router.get("/{character_id}/chats")
async def list_character_chats(
    character_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    from app.services.conversation_service import ConversationService
    svc = CharacterService(db)
    if await svc.get(character_id) is None:
        raise HTTPException(404, "Character not found")
    # reuse conversation list filtered
    cursor = await db.execute(
        """
        SELECT c.*, ch.name AS character_name, p.profile_name AS persona_profile_name
        FROM conversations c
        LEFT JOIN characters ch ON ch.id = c.character_id
        LEFT JOIN personas p ON p.id = c.persona_id
        WHERE c.character_id = ? AND c.is_archived = 0
        ORDER BY COALESCE(c.last_message_at, c.updated_at) DESC
        """,
        (character_id,),
    )
    rows = await cursor.fetchall()
    out = []
    for row in rows:
        out.append({
            "id": row["id"],
            "title": row["title"],
            "character_id": row["character_id"],
            "persona_id": row["persona_id"],
            "persona_display_name": row["persona_display_name"],
            "character_name": row["character_name"],
            "persona_profile_name": row["persona_profile_name"],
            "last_message_at": row["last_message_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })
    return out
