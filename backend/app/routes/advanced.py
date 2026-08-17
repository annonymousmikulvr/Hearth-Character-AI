from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import aiosqlite

from app.database import get_db_dependency
from app.services.advanced_chat import AdvancedChatService
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.schemas.common import MessageResponse

router = APIRouter()


class RateBody(BaseModel):
    rating: Optional[int] = Field(None, description="-1, 1, or null to clear")


class IntensityBody(BaseModel):
    value: float = Field(..., ge=0, le=1)


class PinBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class MuteBody(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)


class BranchBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    icon: str = Field("🌿", max_length=8)
    from_message_id: Optional[str] = None


class SceneBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class ToneRegenBody(BaseModel):
    tone: str = Field(..., pattern="^(soft|sharp|playful|angsty|formal)$")


class PersonaModeBody(BaseModel):
    mode: Optional[str] = None


@router.post("/conversations/{conversation_id}/messages/{message_id}/rate")
async def rate_message(
    conversation_id: str,
    message_id: str,
    body: RateBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    msg = await svc.get_message(message_id)
    if not msg or msg.conversation_id != conversation_id:
        raise HTTPException(404, "Message not found")
    await AdvancedChatService(db).rate_message(message_id, body.rating)
    return {"ok": True, "rating": body.rating}


@router.post("/conversations/{conversation_id}/intensity")
async def set_intensity(
    conversation_id: str,
    body: IntensityBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    val = await AdvancedChatService(db).set_intensity(conversation_id, body.value)
    return {"emotion_intensity": val}


@router.get("/conversations/{conversation_id}/pins")
async def get_pins(
    conversation_id: str, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    return {"pins": await AdvancedChatService(db).get_pins(conversation_id)}


@router.post("/conversations/{conversation_id}/pins")
async def add_pin(
    conversation_id: str,
    body: PinBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    pins = await AdvancedChatService(db).add_pin(conversation_id, body.text)
    return {"pins": pins}


@router.delete("/conversations/{conversation_id}/pins")
async def clear_or_remove_pin(
    conversation_id: str,
    text: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    adv = AdvancedChatService(db)
    if text:
        pins = [p for p in await adv.get_pins(conversation_id) if p != text]
        pins = await adv.set_pins(conversation_id, pins)
    else:
        pins = await adv.set_pins(conversation_id, [])
    return {"pins": pins}


@router.get("/conversations/{conversation_id}/mutes")
async def get_mutes(
    conversation_id: str, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    return {"mutes": await AdvancedChatService(db).get_mutes(conversation_id)}


@router.post("/conversations/{conversation_id}/mutes")
async def add_mute(
    conversation_id: str,
    body: MuteBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    return {"mutes": await AdvancedChatService(db).add_mute(conversation_id, body.topic)}


@router.delete("/conversations/{conversation_id}/mutes/{topic}")
async def remove_mute(
    conversation_id: str,
    topic: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    return {"mutes": await AdvancedChatService(db).remove_mute(conversation_id, topic)}


@router.get("/conversations/{conversation_id}/branches")
async def list_branches(
    conversation_id: str, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    return await AdvancedChatService(db).list_branches(conversation_id)


@router.post("/conversations/{conversation_id}/branches")
async def create_branch(
    conversation_id: str,
    body: BranchBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    return await AdvancedChatService(db).create_branch(
        conversation_id,
        body.name,
        icon=body.icon,
        from_message_id=body.from_message_id,
    )


@router.post("/conversations/{conversation_id}/branches/{branch_id}/activate")
async def activate_branch(
    conversation_id: str,
    branch_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    await AdvancedChatService(db).set_active_branch(conversation_id, branch_id)
    return MessageResponse(message="Branch activated")


@router.post("/conversations/{conversation_id}/scene", status_code=201)
async def post_scene_header(
    conversation_id: str,
    body: SceneBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """Separate scene/world beat — not spoken by the character."""
    svc = ConversationService(db)
    conv = await svc.get(conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    msg = await svc._insert_message(
        conversation_id=conversation_id,
        role="system",
        speaker_type="system",
        speaker_name="Scene",
        raw_content=body.text.strip(),
        content_format="plain",
    )
    # mark scene header if column exists
    try:
        await db.execute(
            "UPDATE messages SET is_scene_header = 1 WHERE id = ?", (msg.id,)
        )
        await db.commit()
    except Exception:
        pass
    return {
        "id": msg.id,
        "role": msg.role,
        "speaker_type": "system",
        "speaker_name": "Scene",
        "raw_content": msg.raw_content,
        "is_scene_header": True,
    }


@router.post("/conversations/{conversation_id}/messages/{message_id}/tone-regen")
async def tone_regenerate(
    conversation_id: str,
    message_id: str,
    body: ToneRegenBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    from app.services.chat_runtime import ChatRuntime

    runtime = ChatRuntime(db)
    # Stash tone on a short-lived approach: prepend system avoid + tone via regenerate
    # We call regenerate after injecting a system note for tone
    svc = ConversationService(db)
    conv = await svc.get(conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    await svc._insert_message(
        conversation_id=conversation_id,
        role="system",
        speaker_type="system",
        speaker_name="System",
        raw_content=f"[Tone request for next regen: {body.tone}]",
        content_format="plain",
    )
    try:
        msgs = await runtime.regenerate(conversation_id, message_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    from app.routes.conversations import _msg_out

    return {"messages": [_msg_out(m) for m in msgs], "tone": body.tone}


@router.post("/memories/{memory_id}/pin")
async def pin_memory(
    memory_id: str,
    pinned: bool = True,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    try:
        await db.execute(
            "UPDATE memories SET is_pinned = ? WHERE id = ?",
            (1 if pinned else 0, memory_id),
        )
        await db.commit()
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "is_pinned": pinned}


class LiveOverridesBody(BaseModel):
    age: Optional[str] = None
    clothes: Optional[str] = None
    side_name: Optional[str] = None
    side_age: Optional[str] = None
    side_clothes: Optional[str] = None
    age_delta: Optional[int] = None  # e.g. +1 year


@router.get("/conversations/{conversation_id}/live-overrides")
async def get_live_overrides(
    conversation_id: str, db: aiosqlite.Connection = Depends(get_db_dependency)
):
    import json
    try:
        cursor = await db.execute("PRAGMA table_info(conversations)")
        cols = {r[1] for r in await cursor.fetchall()}
        if "live_overrides" not in cols:
            await db.execute("ALTER TABLE conversations ADD COLUMN live_overrides TEXT")
            await db.commit()
        cursor = await db.execute(
            "SELECT live_overrides FROM conversations WHERE id = ?", (conversation_id,)
        )
        row = await cursor.fetchone()
        if not row or not row[0]:
            return {}
        return json.loads(row[0])
    except Exception:
        return {}


@router.post("/conversations/{conversation_id}/live-overrides")
async def set_live_overrides(
    conversation_id: str,
    body: LiveOverridesBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    import json
    cursor = await db.execute("PRAGMA table_info(conversations)")
    cols = {r[1] for r in await cursor.fetchall()}
    if "live_overrides" not in cols:
        await db.execute("ALTER TABLE conversations ADD COLUMN live_overrides TEXT")
        await db.commit()
    cursor = await db.execute(
        "SELECT live_overrides FROM conversations WHERE id = ?", (conversation_id,)
    )
    row = await cursor.fetchone()
    data = {}
    if row and row[0]:
        try:
            data = json.loads(row[0]) or {}
        except Exception:
            data = {}
    if body.age is not None:
        data["age"] = body.age
    if body.clothes is not None:
        data["clothes"] = body.clothes
    if body.age_delta is not None:
        try:
            cur = int(str(data.get("age") or "0").split()[0])
            data["age"] = str(cur + body.age_delta)
        except Exception:
            data["age"] = f"+{body.age_delta} years from card"
    if body.side_name:
        sides = data.get("sides") or {}
        info = sides.get(body.side_name) or {}
        if body.side_age is not None:
            info["age"] = body.side_age
        if body.side_clothes is not None:
            info["clothes"] = body.side_clothes
        if body.age_delta is not None and body.side_age is None:
            try:
                cur = int(str(info.get("age") or "0").split()[0])
                info["age"] = str(cur + body.age_delta)
            except Exception:
                info["age"] = f"+{body.age_delta} years"
        sides[body.side_name] = info
        data["sides"] = sides
    await db.execute(
        "UPDATE conversations SET live_overrides = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(data), conversation_id),
    )
    await db.commit()
    return data
