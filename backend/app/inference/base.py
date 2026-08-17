"""
Inference provider abstraction.
All model execution goes through this interface so character/chat logic
never depends on a specific runtime (Ollama, llama.cpp, …).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GenerationRequest:
    """Fully prepared request for the inference engine."""

    model: str
    messages: list[dict[str, str]]  # [{role, content}, ...]
    temperature: float = 0.85
    top_p: float = 0.9
    max_tokens: int = 512
    repetition_penalty: float = 1.1
    stop: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Complete response from the model (never partial)."""

    content: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    duration_ms: Optional[int] = None
    raw: Optional[dict[str, Any]] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.content)


class InferenceProvider(ABC):
    """Abstract local inference backend."""

    name: str = "base"

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        ...

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate a *complete* response. Do not stream to the caller."""
        ...
