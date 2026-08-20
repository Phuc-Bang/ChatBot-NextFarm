"""Tang goi model. Xem base.py de biet vi sao co interface nay."""

from __future__ import annotations

from app.core.config import lay
from app.services.llm.base import KetQuaLLM, LLMClient

__all__ = ["KetQuaLLM", "LLMClient", "tao_client"]


def tao_client(provider: str | None = None, model: str | None = None):
    """Tao client theo .env.

    Doi model = doi mot dong .env, khong sua code (DEC-015).
    """
    provider = (provider or lay("LLM_PROVIDER", "gemini") or "gemini").lower()
    if provider == "gemini":
        from app.services.llm.gemini import GeminiClient
        return GeminiClient(model=model or lay("LLM_MODEL"))
    raise ValueError(
        "Chua ho tro provider '" + provider + "'. Dang co: gemini.")
