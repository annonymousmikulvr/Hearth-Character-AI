from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import aiosqlite

from app.database import get_db_dependency
from app.services.world_service import WorldService
from app.schemas.common import MessageResponse

router = APIRouter()


class WorldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    rules: Optional[str] = None
    lore: Optional[str] = None
    locations: list[Any] = Field(default_factory=list)
    factions: list[Any] = Field(default_factory=list)
    objects: list[Any] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class WorldUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    rules: Optional[str] = None
    lore: Optional[str] = None
    locations: Optional[list[Any]] = None
    factions: Optional[list[Any]] = None
    objects: Optional[list[Any]] = None
    tags: Optional[list[str]] = None
    is_archived: Optional[bool] = None


class WorldOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    rules: Optional[str] = None
    lore: Optional[str] = None
    locations: list[Any] = Field(default_factory=list)
    factions: list[Any] = Field(default_factory=list)
    objects: list[Any] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_archived: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


def _out(w) -> WorldOut:
    return WorldOut(
        id=w.id,
        name=w.name,
        description=w.description,
        rules=w.rules,
        lore=w.lore,
        locations=w.locations,
        factions=w.factions,
        objects=w.objects,
        tags=w.tags,
        is_archived=w.is_archived,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


@router.get("", response_model=list[WorldOut])
async def list_worlds(db: aiosqlite.Connection = Depends(get_db_dependency)):
    return [_out(w) for w in await WorldService(db).list()]


@router.post("", response_model=WorldOut, status_code=201)
async def create_world(
    body: WorldCreate, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    w = await WorldService(db).create(body.model_dump())
    return _out(w)


@router.get("/{world_id}", response_model=WorldOut)
async def get_world(
    world_id: str, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    w = await WorldService(db).get(world_id)
    if not w:
        raise HTTPException(404, "World not found")
    return _out(w)


@router.patch("/{world_id}", response_model=WorldOut)
async def update_world(
    world_id: str,
    body: WorldUpdate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    w = await WorldService(db).update(world_id, body.model_dump(exclude_unset=True))
    if not w:
        raise HTTPException(404, "World not found")
    return _out(w)


@router.delete("/{world_id}", response_model=MessageResponse)
async def delete_world(
    world_id: str, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    ok = await WorldService(db).delete(world_id)
    if not ok:
        raise HTTPException(404, "World not found")
    return MessageResponse(message="World archived")
