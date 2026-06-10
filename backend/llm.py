import config


def generate(system_prompt: str, user_prompt: str) -> str:
    if config.CHAT_PROVIDER == "anthropic":
        from anthropic_client import generate as _generate
    else:
        from gemini_client import generate as _generate
    return _generate(system_prompt, user_prompt)
