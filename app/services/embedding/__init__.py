"""Tang embedding. Xem base.py de biet vi sao chay local."""

from __future__ import annotations

from app.services.embedding.base import EmbeddingModel, cosine

__all__ = ["EmbeddingModel", "cosine", "tao_embedding"]


def tao_embedding(ten: str | None = None, **kw):
    from app.core.config import lay
    from app.services.embedding.local import LocalEmbedding
    return LocalEmbedding(ten or lay("EMBEDDING_MODEL") or "halong", **kw)
