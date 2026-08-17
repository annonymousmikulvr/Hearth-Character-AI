"""
Local AI / Ollama configuration and diagnostics.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import aiosqlite

from app.database import get_db_dependency
from app.inference.ollama import get_ollama_provider
from app.services.settings_service import SettingsService

router = APIRouter()


class AIConfigUpdate(BaseModel):
    ollama_base_url: Optional[str] = Field(None, max_length=200)
    default_model: Optional[str] = Field(None, max_length=200)
    default_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    default_top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    default_repetition_penalty: Optional[float] = Field(None, ge=0.5, le=2.0)
    default_max_tokens: Optional[int] = Field(None, ge=16, le=8192)


class TestGenerateRequest(BaseModel):
    model: Optional[str] = None
    prompt: str = Field("Say hello in one short sentence.", max_length=2000)


@router.get("/connection")
async def connection_status(db: aiosqlite.Connection = Depends(get_db_dependency)):
    svc = SettingsService(db)
    base_url = await svc.get("ollama_base_url") or "http://127.0.0.1:11434"
    provider = get_ollama_provider(base_url)
    available = await provider.is_available()
    models = await provider.list_models() if available else []
    return {
        "provider": "ollama",
        "base_url": base_url,
        "available": available,
        "models": models,
        "default_model": await svc.get("default_model") or "",
    }


@router.get("/models")
async def list_models(db: aiosqlite.Connection = Depends(get_db_dependency)):
    svc = SettingsService(db)
    base_url = await svc.get("ollama_base_url") or "http://127.0.0.1:11434"
    provider = get_ollama_provider(base_url)
    if not await provider.is_available():
        raise HTTPException(
            503,
            f"Ollama is not reachable at {base_url}. Start Ollama first.",
        )
    models = await provider.list_models()
    return {"models": models, "base_url": base_url}


@router.post("/config")
async def update_ai_config(
    body: AIConfigUpdate,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    svc = SettingsService(db)
    if body.ollama_base_url is not None:
        await svc.set("ollama_base_url", body.ollama_base_url.rstrip("/"))
    if body.default_model is not None:
        await svc.set("default_model", body.default_model)
    if body.default_temperature is not None:
        await svc.set("default_temperature", str(body.default_temperature))
    if body.default_top_p is not None:
        await svc.set("default_top_p", str(body.default_top_p))
    if body.default_repetition_penalty is not None:
        await svc.set(
            "default_repetition_penalty", str(body.default_repetition_penalty)
        )
    if body.default_max_tokens is not None:
        await svc.set("default_max_tokens", str(body.default_max_tokens))
    return {"ok": True}


@router.post("/test")
async def test_generate(
    body: TestGenerateRequest,
    db: aiosqlite.Connection = Depends(get_db_dependency),
):
    """Run a short generation to verify the local model works."""
    from app.inference.base import GenerationRequest

    svc = SettingsService(db)
    base_url = await svc.get("ollama_base_url") or "http://127.0.0.1:11434"
    model = body.model or (await svc.get("default_model") or "")
    if not model:
        raise HTTPException(
            400,
            "No model specified and no default_model configured.",
        )

    provider = get_ollama_provider(base_url)
    if not await provider.is_available():
        raise HTTPException(503, f"Ollama not reachable at {base_url}")

    result = await provider.generate(
        GenerationRequest(
            model=model,
            messages=[{"role": "user", "content": body.prompt}],
            temperature=0.7,
            max_tokens=64,
        )
    )
    if not result.ok:
        raise HTTPException(502, result.error or "Generation failed")
    return {
        "content": result.content,
        "model": result.model,
        "duration_ms": result.duration_ms,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
    }
