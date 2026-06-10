import time
from typing import List

from google import genai
from google.genai import types

import config

_client: genai.Client | None = None


def client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.require_api_key())
    return _client


def embed_texts(texts: List[str], *, task_type: str, batch_size: int = 100) -> List[List[float]]:
    out: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = _with_retry(
            lambda: client().models.embed_content(
                model=config.EMBED_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )
        )
        out.extend([e.values for e in resp.embeddings])
    return out


def generate(system_prompt: str, user_prompt: str) -> str:
    resp = _with_retry(
        lambda: client().models.generate_content(
            model=config.CHAT_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
    )
    return (resp.text or "").strip()


def _with_retry(fn, attempts: int = 4, base_delay: float = 1.0):
    last = None
    for n in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            msg = str(e).lower()
            transient = any(s in msg for s in ("429", "503", "500", "timeout", "deadline", "unavailable"))
            if not transient or n == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** n))
    raise last
