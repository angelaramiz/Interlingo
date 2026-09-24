from ..config import settings


def chat_json(messages: list[dict]) -> dict:
    if settings.ai_provider == "local":
        from .local import local_chat_json

        return local_chat_json(messages)
    from .orcarouter import orcarouter

    return orcarouter.chat_json(messages)