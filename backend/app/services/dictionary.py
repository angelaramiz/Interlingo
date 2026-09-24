from ..ai.inference import chat_json
from ..ai.prompts import diccionario as diccionario_prompt

MAX_PALABRA_LEN = 100


def traducir_palabra(
    palabra: str | None,
    idioma_objetivo: str = "en",
    idioma_nativo: str = "es",
    contexto: str = "",
) -> dict:
    normalizada = (palabra or "").strip()
    if not normalizada:
        raise ValueError("palabra vacía")
    if len(normalizada) > MAX_PALABRA_LEN:
        raise ValueError("palabra demasiado larga")
    msgs = diccionario_prompt(normalizada, idioma_objetivo, idioma_nativo, contexto or "")
    data = chat_json(msgs)
    return {
        "termino": data.get("termino", normalizada) or normalizada,
        "traduccion": data.get("traduccion", "") or "",
        "definicion": data.get("definicion", "") or "",
        "ejemplo": data.get("ejemplo", "") or "",
    }
