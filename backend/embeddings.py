"""Local, on-device embeddings — no API key, no cost. Used for retrieval."""
from typing import List

from fastembed import TextEmbedding

import config

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        cache_dir = config.STORE_DIR / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        _model = TextEmbedding(model_name=config.EMBED_MODEL, cache_dir=str(cache_dir))
    return _model


def embed_texts(texts: List[str], *, task_type: str | None = None, batch_size: int = 256) -> List[List[float]]:
    # task_type is accepted for API compatibility but unused for the local model.
    model = _get_model()
    return [vec.tolist() for vec in model.embed(texts, batch_size=batch_size)]
