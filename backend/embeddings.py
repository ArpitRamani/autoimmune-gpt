"""Embeddings for retrieval. Provider is chosen by EMBED_PROVIDER:
  - "local"  : on-device fastembed model (no API key, no cost)  [default]
  - "gemini" : Google text-embedding-004 (needs GEMINI_API_KEY)
"""
from typing import List

import config

_local_model = None


def embed_texts(texts: List[str], *, task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
    if config.EMBED_PROVIDER == "gemini":
        from gemini_client import embed_texts as gemini_embed
        return gemini_embed(texts, task_type=task_type)
    return _embed_local(texts)


def _embed_local(texts: List[str], batch_size: int = 256) -> List[List[float]]:
    global _local_model
    if _local_model is None:
        from fastembed import TextEmbedding
        cache_dir = config.STORE_DIR / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        _local_model = TextEmbedding(model_name=config.LOCAL_EMBED_MODEL, cache_dir=str(cache_dir))
    return [vec.tolist() for vec in _local_model.embed(texts, batch_size=batch_size)]
