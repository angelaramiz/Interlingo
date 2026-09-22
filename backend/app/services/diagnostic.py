import json

from sqlalchemy.orm import Session

from ..ai.inference import chat_json
from ..ai.prompts import diagnostico
from ..ai.prompts import interpretar_meta as interpretar_meta_prompt


def interpretar_meta(db: Session, meta) -> dict:
    msgs = interpretar_meta_prompt(meta.texto, meta.idioma_objetivo)
    data = chat_json(msgs)
    meta.tema = data["tema"]
    meta.estado = "diagnostico"
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return data


def generar_diagnostico(db: Session, meta) -> dict:
    msgs = diagnostico(meta.tema, _conceptos(meta), meta.idioma_objetivo)
    data = chat_json(msgs)
    return data


def procesar_diagnostico(db: Session, meta, respuestas: list[str]) -> dict:
    resumen = json.dumps({"preguntas": len(respuestas), "respuestas": respuestas})
    meta.estado = "plan"
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return {"resumen": resumen}


def _conceptos(meta) -> list[str]:
    if meta.tema:
        return [meta.tema]
    return []
