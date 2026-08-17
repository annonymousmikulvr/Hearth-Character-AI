from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import aiosqlite

from app.database import get_db_dependency
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationOut,
    ConversationListItem,
    MessageCreate,
    MessageOut,
)
from app.schemas.common import MessageResponse
from app.services.conversation_service import ConversationService

router = APIRouter()


def _conv_out(c) -> ConversationOut:
    return ConversationOut(
        id=c.id,
        title=c.title,
        character_id=c.character_id,
        persona_id=c.persona_id,
        persona_display_name=c.persona_display_name,
        world_id=c.world_id,
        temperature=c.temperature,
        top_p=c.top_p,
        repetition_penalty=c.repetition_penalty,
        max_tokens=c.max_tokens,
        model_name=c.model_name,
        is_archived=c.is_archived,
        last_message_at=c.last_message_at,
        created_at=c.created_at,
        updated_at=c.updated_at,
        character_name=c.character_name,
        persona_profile_name=c.persona_profile_name,
        seed_notes=getattr(c, 'seed_notes', None),
        is_custom=getattr(c, 'is_custom', False),
        filter_level=getattr(c, 'filter_level', None),
    )


def _msg_out(m) -> MessageOut:
    return MessageOut(
        id=m.id,
        conversation_id=m.conversation_id,
        role=m.role,
        speaker_type=m.speaker_type,
        speaker_id=m.speaker_id,
        speaker_name=m.speaker_name,
        raw_content=m.raw_content,
        content_format=m.content_format,
        parent_message_id=m.parent_message_id,
        variant_index=m.variant_index,
        is_selected_variant=m.is_selected_variant,
        temperature=m.temperature,
        max_tokens=m.max_tokens,
        model_name=m.model_name,
        token_count=m.token_count,
        generation_ms=m.generation_ms,
        created_at=m.created_at,
    )


@router.get("", response_model=list[ConversationListItem])
async def list_conversations(
    include_archived: bool = False,
    character_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    convs = await svc.list(
        include_archived=include_archived,
        character_id=character_id,
        limit=limit,
        offset=offset,
    )
    return [
        ConversationListItem(
            id=c.id,
            title=c.title,
            character_id=c.character_id,
            character_name=c.character_name,
            persona_id=c.persona_id,
            persona_display_name=c.persona_display_name,
            persona_profile_name=c.persona_profile_name,
            is_archived=c.is_archived,
            last_message_at=c.last_message_at,
            updated_at=c.updated_at,
        )
        for c in convs
    ]


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    try:
        conv = await svc.create(body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _conv_out(conv)



class PresetRequest(BaseModel):
    character_id: str
    persona_id: str
    situation: Optional[str] = None


@router.post("/generate-preset")
async def generate_chat_preset(
    body: PresetRequest,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """
    Build an editable starter seed script from character + persona.
    Uses a smart template first; optionally polishes with the local model if available.
    """
    from app.services.character_service import CharacterService
    from app.services.persona_service import PersonaService
    from app.services.settings_service import SettingsService
    from app.inference.ollama import OllamaProvider
    from app.inference.base import GenerationRequest

    char = await CharacterService(db).get(body.character_id)
    persona = await PersonaService(db).get(body.persona_id)
    if not char or not persona:
        raise HTTPException(404, "Character or persona not found")

    char_name = char.name
    user_name = persona.chat_name or persona.profile_name or "User"
    traits = ", ".join((char.traits or [])[:6]) if getattr(char, "traits", None) else ""
    speaking = getattr(char, "speaking_style", None) or getattr(char, "baseline_personality", None) or getattr(char, "system_prompt", None) or "in character"
    situation = (body.situation or "").strip() or "They run into each other casually."

    # Template preset (always available offline)
    template_script = f"""Char: *{{char}} approaches {{user}} and rests a hand lightly on their shoulder.* — "Hey {{user}}, what's up?"
User: — "Hey {{char}}, nothin' much. What about you?"
Char: *{{char}} tilts their head, studying {{user}} for a second.* — "Same as always. You free for a bit?"
User: — "Yeah, I can stick around."
Char: *{{char}} lets out a small breath that might be a laugh.* — "Good. There's something I wanted to talk about."
"""

    template_notes = (
        f"Opening scene: {situation}\n"
        f"Character: {char_name}. Persona in chat as: {user_name}.\n"
        f"Keep first person for {char_name}. Use — \"dialogue\" and *actions*."
    )

    # Optional model polish
    polished_script = None
    try:
        settings = SettingsService(db)
        model = await settings.get("default_model") or "llama3.2"
        base = await settings.get("ollama_base_url") or "http://127.0.0.1:11434"
        provider = OllamaProvider(base_url=base)
        prompt = (
            "Write a short roleplay seed conversation (4–6 lines) between Char and User.\n"
            "Format EACH line exactly like:\n"
            'Char: *action in first person or bare verb.* — "dialogue"\n'
            'User: — "dialogue"\n'
            "Rules:\n"
            "- Char is first person actions (*I wave.* or *waves.*), never third-person name as subject.\n"
            "- Use {{char}} and {{user}} placeholders in dialogue when addressing each other.\n"
            "- Match Char's voice.\n"
            f"Char name: {char_name}\n"
            f"Char personality: {(getattr(char, 'baseline_personality', None) or getattr(char, 'system_prompt', None) or '')[:400]}\n"
            f"Traits: {traits}\n"
            f"Speaking style: {str(speaking)[:200]}\n"
            f"User persona name: {user_name}\n"
            f"Persona facts: {', '.join((persona.additional_facts or [])[:5])}\n"
            f"Situation: {situation}\n"
            "Output ONLY the script lines, no intro."
        )
        result = await provider.generate(
            GenerationRequest(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.85,
                max_tokens=400,
            )
        )
        text = (result.content or "").strip()
        # Keep only valid lines
        lines = []
        for line in text.splitlines():
            if line.strip().lower().startswith(("char:", "user:", "system:")):
                lines.append(line.strip())
        if len(lines) >= 2:
            polished_script = "\n".join(lines)
    except Exception:
        polished_script = None

    return {
        "seed_script": polished_script or template_script,
        "seed_notes": template_notes,
        "source": "model" if polished_script else "template",
        "character_name": char_name,
        "user_name": user_name,
    }



@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    conv = await svc.get(conversation_id)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    return _conv_out(conv)


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    conv = await svc.update(conversation_id, body)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    return _conv_out(conv)


@router.delete("/{conversation_id}", response_model=MessageResponse)
async def delete_conversation(
    conversation_id: str,
    hard: bool = False,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    ok = await svc.delete(conversation_id, hard=hard)
    if not ok:
        raise HTTPException(404, "Conversation not found")
    return MessageResponse(
        message="Conversation deleted" if hard else "Conversation archived"
    )


# ── Messages nested under conversation ───────────────────────

@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: str,
    selected_only: bool = True,
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    conv = await svc.get(conversation_id)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    messages = await svc.list_messages(
        conversation_id,
        selected_only=selected_only,
        limit=limit,
        offset=offset,
    )
    return [_msg_out(m) for m in messages]


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=201,
)
async def post_message(
    conversation_id: str,
    body: MessageCreate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    try:
        msg = await svc.add_user_message(conversation_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _msg_out(msg)


class GenerateResponse(BaseModel):
    messages: list[MessageOut]
    state: str = "complete"


class MessageEditBody(BaseModel):
    raw_content: str


@router.post(
    "/{conversation_id}/generate",
    response_model=GenerateResponse,
)
async def generate_reply(
    conversation_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """
    Generate a complete assistant reply (possibly multiple speaker turns).
    Full response only — no token streaming.
    """
    from app.services.chat_runtime import ChatRuntime

    runtime = ChatRuntime(db)
    try:
        msgs = await runtime.generate_reply(conversation_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return GenerateResponse(messages=[_msg_out(m) for m in msgs], state="complete")





@router.post("/{conversation_id}/hint")
async def user_hint(
    conversation_id: str,
    count: int = 3,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """Suggest user replies (persona + history + last AI). Not auto-sent."""
    from app.services.chat_runtime import ChatRuntime
    runtime = ChatRuntime(db)
    try:
        options = await runtime.generate_user_hint(conversation_id, count=count)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"hints": options}

@router.post("/{conversation_id}/continue")
async def continue_reply(
    conversation_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """Bot continues from its last message without a new user line."""
    from app.services.chat_runtime import ChatRuntime
    runtime = ChatRuntime(db)
    try:
        msgs = await runtime.continue_reply(conversation_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    return GenerateResponse(messages=[_msg_out(m) for m in msgs])


@router.post(
    "/{conversation_id}/messages/{message_id}/regenerate",
    response_model=GenerateResponse,
)
async def regenerate_message(
    conversation_id: str,
    message_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """
    Regenerate an assistant message as a new variant.
    Prior variants are kept and passed to the model as text to avoid.
    """
    from app.services.chat_runtime import ChatRuntime

    runtime = ChatRuntime(db)
    try:
        msgs = await runtime.regenerate(conversation_id, message_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return GenerateResponse(messages=[_msg_out(m) for m in msgs], state="complete")


@router.get(
    "/{conversation_id}/messages/{message_id}/variants",
    response_model=list[MessageOut],
)
async def list_variants(
    conversation_id: str,
    message_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    msg = await svc.get_message(message_id)
    if msg is None or msg.conversation_id != conversation_id:
        raise HTTPException(404, "Message not found")
    root = msg.parent_message_id or msg.id
    variants = await svc.list_variants(root)
    return [_msg_out(m) for m in variants]


@router.post(
    "/{conversation_id}/messages/{message_id}/select",
    response_model=MessageOut,
)
async def select_variant(
    conversation_id: str,
    message_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    msg = await svc.get_message(message_id)
    if msg is None or msg.conversation_id != conversation_id:
        raise HTTPException(404, "Message not found")
    selected = await svc.select_variant(message_id)
    return _msg_out(selected)


@router.patch(
    "/{conversation_id}/messages/{message_id}",
    response_model=MessageOut,
)
async def edit_message(
    conversation_id: str,
    message_id: str,
    body: MessageEditBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    if not body.raw_content.strip():
        raise HTTPException(400, "raw_content cannot be empty")
    svc = ConversationService(db)
    msg = await svc.get_message(message_id)
    if msg is None or msg.conversation_id != conversation_id:
        raise HTTPException(404, "Message not found")
    updated = await svc.edit_message(message_id, body.raw_content.strip())
    return _msg_out(updated)


class InjectBody(BaseModel):
    speaker_type: str = "side"  # primary | side | system
    speaker_name: str = "Narrator"
    raw_content: str
    role: str = "assistant"


@router.post("/{conversation_id}/inject", response_model=MessageOut, status_code=201)
async def inject_message(
    conversation_id: str,
    body: InjectBody,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """Dev/tooling: insert a message with explicit speaker metadata."""
    svc = ConversationService(db)
    conv = await svc.get(conversation_id)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    role = body.role if body.role in ("assistant", "system", "user") else "assistant"
    speaker_type = body.speaker_type if body.speaker_type in ("primary", "side", "system", "user") else "side"
    msg = await svc._insert_message(
        conversation_id=conversation_id,
        role=role,
        speaker_type=speaker_type,
        speaker_id=conv.character_id if speaker_type == "primary" else None,
        speaker_name=body.speaker_name or "Unknown",
        raw_content=body.raw_content,
    )
    return _msg_out(msg)



@router.delete("/{conversation_id}/messages/{message_id}", response_model=MessageResponse)
async def delete_message(
    conversation_id: str,
    message_id: str,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = ConversationService(db)
    ok = await svc.delete_message_family(conversation_id, message_id)
    if not ok:
        # fallback single delete
        msg = await svc.get_message(message_id)
        if msg is None or msg.conversation_id != conversation_id:
            raise HTTPException(404, "Message not found")
        await svc.delete_message(message_id)
    return MessageResponse(message="Message deleted")


class RewindBody(BaseModel):
    include_message: bool = True


@router.post("/{conversation_id}/messages/{message_id}/rewind", response_model=MessageResponse)
async def rewind_messages(
    conversation_id: str,
    message_id: str,
    body: RewindBody = RewindBody(),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """Delete all messages after this one. Set include_message=false to remove it too."""
    svc = ConversationService(db)
    try:
        n = await svc.rewind_to_message(
            conversation_id, message_id, include_message=body.include_message
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    return MessageResponse(message=f"Removed {n} message(s)")
