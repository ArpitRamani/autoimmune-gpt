import time

from google import genai
from google.genai import types

import config

# Optional fallback chat provider (CHAT_PROVIDER=gemini). The default is Anthropic.
_client: genai.Client | None = None


def client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.require_api_key())
    return _client


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
