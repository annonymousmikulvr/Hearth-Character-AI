"""Optional local image generation (Automatic1111 / SD-compatible API)."""

from __future__ import annotations

import base64
import uuid
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import aiosqlite

from app.database import get_db_dependency
from app.services.settings_service import SettingsService
from app.services.character_service import CharacterService

router = APIRouter()

MEDIA_ROOT = Path(__file__).resolve().parents[2] / "data" / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


class ImageGenRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: Optional[str] = Field(None, max_length=2000)
    character_id: Optional[str] = None
    width: int = Field(512, ge=256, le=1024)
    height: int = Field(512, ge=256, le=1024)
    steps: int = Field(20, ge=5, le=50)


class ImageGenResponse(BaseModel):
    ok: bool
    path: Optional[str] = None
    error: Optional[str] = None


@router.get("/status")
async def image_status(db: aiosqlite.Connection = Depends(get_db_dependency)):
    settings = SettingsService(db)
    enabled = (await settings.get("image_backend_enabled") or "false").lower() == "true"
    url = await settings.get("image_backend_url") or ""
    reachable = False
    if enabled and url:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{url.rstrip('/')}/sdapi/v1/sd-models")
                reachable = r.status_code == 200
        except Exception:
            reachable = False
    return {
        "enabled": enabled,
        "base_url": url,
        "reachable": reachable,
        "required": False,
    }


@router.post("/generate", response_model=ImageGenResponse)
async def generate_image(
    body: ImageGenRequest,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    settings = SettingsService(db)
    enabled = (await settings.get("image_backend_enabled") or "false").lower() == "true"
    url = (await settings.get("image_backend_url") or "").rstrip("/")
    if not enabled or not url:
        return ImageGenResponse(
            ok=False,
            error="Image backend disabled. Set image_backend_url and enable in Settings.",
        )

    prompt = body.prompt
    if body.character_id:
        ch = await CharacterService(db).get(body.character_id)
        if ch and ch.image_gen_style:
            prompt = f"{prompt}, {ch.image_gen_style}"
        if ch and not ch.image_gen_enabled:
            return ImageGenResponse(ok=False, error="Image gen disabled for this character.")

    payload = {
        "prompt": prompt,
        "negative_prompt": body.negative_prompt or "blurry, low quality",
        "width": body.width,
        "height": body.height,
        "steps": body.steps,
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{url}/sdapi/v1/txt2img", json=payload)
            r.raise_for_status()
            data = r.json()
        images = data.get("images") or []
        if not images:
            return ImageGenResponse(ok=False, error="No image returned")
        raw = base64.b64decode(images[0].split(",")[-1] if isinstance(images[0], str) else images[0])
        name = f"gen_{uuid.uuid4().hex}.png"
        path = MEDIA_ROOT / name
        path.write_bytes(raw)
        return ImageGenResponse(ok=True, path=f"/api/images/media/{name}")
    except Exception as e:
        return ImageGenResponse(ok=False, error=str(e))


@router.post("/characters/{character_id}/avatar")
async def upload_avatar(
    character_id: str,
    file: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = CharacterService(db)
    ch = await svc.get(character_id)
    if not ch:
        raise HTTPException(404, "Character not found")
    data = await file.read()
    if len(data) > 8_000_000:
        raise HTTPException(400, "File too large (max 8MB)")
    ext = Path(file.filename or "avatar.png").suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        ext = ".png"
    name = f"avatar_{character_id}{ext}"
    path = MEDIA_ROOT / name
    path.write_bytes(data)
    rel = f"/api/images/media/{name}"
    from app.schemas.character import CharacterUpdate
    await svc.update(character_id, CharacterUpdate(avatar_path=rel))
    return {"avatar_path": rel}


@router.get("/media/{filename}")
async def get_media(filename: str):
    if "/" in filename or ".." in filename:
        raise HTTPException(400, "Invalid path")
    path = MEDIA_ROOT / filename
    if not path.exists():
        raise HTTPException(404, "Not found")
    return FileResponse(path)
