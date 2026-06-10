import time

import anthropic

import config

_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.require_anthropic_key())
    return _client


def generate(system_prompt: str, user_prompt: str) -> str:
    resp = _with_retry(
        lambda: client().messages.create(
            model=config.ANTHROPIC_CHAT_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def _with_retry(fn, attempts: int = 4, base_delay: float = 1.0):
    last = None
    for n in range(attempts):
        try:
            return fn()
        except (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.APIConnectionError) as e:
            last = e
            if n == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** n))
    raise last
