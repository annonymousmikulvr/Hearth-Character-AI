from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import aiosqlite

from app.database import get_db_dependency
from app.services.memory_service import MemoryService
from app.schemas.common import MessageResponse

router = APIRouter()


class MemoryCreate(BaseModel):
    owner_type: str = Field(..., pattern="^(global|character|conversation|world|persona)$")
    owner_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    category: Optional[str] = None
    confidence: float = Field(0.7, ge=0, le=1)
    importance: float = Field(0.5, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)


class MemoryOut(BaseModel):
    id: str
    owner_type: str
    owner_id: str
    content: str
    category: Optional[str] = None
    confidence: float
    importance: float
    tags: list[str] = Field(default_factory=list)
    source_conversation_id: Optional[str] = None
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None


def _out(m) -> MemoryOut:
    return MemoryOut(
        id=m.id,
        owner_type=m.owner_type,
        owner_id=m.owner_id,
        content=m.content,
        category=m.category,
        confidence=m.confidence,
        importance=m.importance,
        tags=m.tags,
        source_conversation_id=m.source_conversation_id,
        created_at=m.created_at,
        last_used_at=m.last_used_at,
    )


@router.get("", response_model=list[MemoryOut])
async def list_memories(
    owner_type: Optional[str] = None,
    owner_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    mems = await MemoryService(db).list(
        owner_type=owner_type, owner_id=owner_id, limit=limit
    )
    return [_out(m) for m in mems]


@router.post("", response_model=MemoryOut, status_code=201)
async def create_memory(
    body: MemoryCreate, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    try:
        m = await MemoryService(db).create(**body.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _out(m)


@router.delete("/{memory_id}", response_model=MessageResponse)
async def delete_memory(
    memory_id: str, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    ok = await MemoryService(db).delete(memory_id)
    if not ok:
        raise HTTPException(404, "Memory not found")
    return MessageResponse(message="Memory archived")
