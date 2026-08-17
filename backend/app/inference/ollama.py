"""
Ollama inference provider.
Talks only to a local Ollama instance (default http://127.0.0.1:11434).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from app.inference.base import (
    GenerationRequest,
    GenerationResult,
    InferenceProvider,
)

logger = logging.getLogger(__name__)


class OllamaProvider(InferenceProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def is_available(self) -> bool:
        try:
            async with self._client() as client:
                r = await client.get("/api/tags")
                return r.status_code == 200
        except Exception as exc:
            logger.debug("Ollama unavailable: %s", exc)
            return False

    async def list_models(self) -> list[str]:
        try:
            async with self._client() as client:
                r = await client.get("/api/tags")
                r.raise_for_status()
                data = r.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as exc:
            logger.warning("Failed to list Ollama models: %s", exc)
            return []

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Call Ollama /api/chat with stream=false so we receive the full reply.
        Generation and UI playback remain separate stages.
        """
        options: dict[str, Any] = {
            "temperature": request.temperature,
            "top_p": request.top_p,
            "num_predict": request.max_tokens,
            "repeat_penalty": request.repetition_penalty,
        }
        # Speed knobs from request.extra
        if request.extra.get("num_ctx"):
            options["num_ctx"] = int(request.extra["num_ctx"])
        if request.extra.get("num_thread"):
            options["num_thread"] = int(request.extra["num_thread"])
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": request.messages,
            "stream": False,
            "keep_alive": request.extra.get("keep_alive", "10m"),
            "options": options,
        }
        if request.stop:
            payload["options"]["stop"] = request.stop

        started = time.perf_counter()
        try:
            async with self._client() as client:
                r = await client.post("/api/chat", json=payload)
                duration_ms = int((time.perf_counter() - started) * 1000)

                if r.status_code != 200:
                    detail = r.text[:500]
                    logger.error("Ollama error %s: %s", r.status_code, detail)
                    return GenerationResult(
                        content="",
                        model=request.model,
                        duration_ms=duration_ms,
                        error=f"Ollama HTTP {r.status_code}: {detail}",
                    )

                data = r.json()
                message = data.get("message") or {}
                content = (message.get("content") or "").strip()

                return GenerationResult(
                    content=content,
                    model=data.get("model") or request.model,
                    prompt_tokens=data.get("prompt_eval_count"),
                    completion_tokens=data.get("eval_count"),
                    total_tokens=(
                        (data.get("prompt_eval_count") or 0)
                        + (data.get("eval_count") or 0)
                    )
                    or None,
                    duration_ms=duration_ms,
                    raw=data,
                )
        except httpx.ConnectError:
            return GenerationResult(
                content="",
                model=request.model,
                error="Cannot connect to Ollama. Is it running on "
                f"{self.base_url}?",
            )
        except httpx.TimeoutException:
            return GenerationResult(
                content="",
                model=request.model,
                error="Ollama request timed out. Try a smaller max_tokens or a faster model.",
            )
        except Exception as exc:
            logger.exception("Ollama generate failed")
            return GenerationResult(
                content="",
                model=request.model,
                error=str(exc),
            )


# Module-level helper used by routes/services
_default_provider: Optional[OllamaProvider] = None


def get_ollama_provider(base_url: Optional[str] = None) -> OllamaProvider:
    global _default_provider
    url = base_url or "http://127.0.0.1:11434"
    if _default_provider is None or _default_provider.base_url != url.rstrip("/"):
        _default_provider = OllamaProvider(base_url=url)
    return _default_provider
