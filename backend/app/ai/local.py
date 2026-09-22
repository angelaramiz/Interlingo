import json
import re

from ..config import settings

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        from llama_cpp import Llama

        _llm = Llama(
            model_path=settings.local_model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False,
        )
    return _llm


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("La respuesta del modelo no contiene JSON válido")
    return json.loads(cleaned[start : end + 1])


def local_chat_json(messages: list[dict]) -> dict:
    llm = _get_llm()
    kwargs = {
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "max_tokens": 1536,
    }
    try:
        resp = llm.create_chat_completion(
            **kwargs, chat_template_kwargs={"enable_thinking": False}
        )
    except TypeError:
        resp = llm.create_chat_completion(**kwargs)
    content = resp["choices"][0]["message"]["content"]
    return _extract_json(content)