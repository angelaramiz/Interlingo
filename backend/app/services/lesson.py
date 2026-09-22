from sqlalchemy.orm import Session

from ..ai.inference import chat_json
from ..ai.prompts import leccion
from ..models import Nivel


def generar_leccion(db: Session, nivel: Nivel) -> dict:
    plan_nivel = {
        "numero": nivel.numero,
        "objetivo": nivel.objetivo,
        "criterio_exito": nivel.criterio_exito,
    }
    meta = nivel.meta
    msgs = leccion(
        meta.tema,
        plan_nivel,
        meta.idioma_objetivo,
        _cefr(meta),
        nivel.numero,
    )
    data = chat_json(msgs)
    nivel.contenido = data["texto"]
    nivel.vocabulario = data.get("vocabulario", [])
    nivel.estado = "pendiente"
    db.add(nivel)
    db.commit()
    db.refresh(nivel)
    return data


def _cefr(meta) -> str:
    return getattr(meta.usuario, "nivel_cefr", "A1") if meta.usuario else "A1"
