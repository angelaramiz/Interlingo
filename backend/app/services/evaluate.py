from sqlalchemy.orm import Session

from ..ai.inference import chat_json
from ..ai.prompts import correccion, evaluacion_pregunta
from ..models import Evaluacion, Nivel


def generar_evaluacion(db: Session, nivel: Nivel) -> dict:
    plan_nivel = {
        "numero": nivel.numero,
        "objetivo": nivel.objetivo,
        "criterio_exito": nivel.criterio_exito,
    }
    meta = nivel.meta
    msgs = evaluacion_pregunta(
        meta.tema,
        plan_nivel,
        meta.idioma_objetivo,
        _cefr(meta),
    )
    data = chat_json(msgs)
    ev = Evaluacion(
        nivel_id=nivel.id,
        tipo=data.get("tipo", "opcion_multiple"),
        pregunta=data["pregunta"],
        opciones=data.get("opciones"),
        respuesta_correcta=data.get("respuesta_correcta", ""),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return {"id": ev.id, "tipo": ev.tipo, "pregunta": ev.pregunta, "opciones": ev.opciones}


def calificar(db: Session, ev: Evaluacion, respuesta: str) -> dict:
    if ev.tipo == "opcion_multiple":
        correcta = _match(ev.respuesta_correcta, respuesta)
    else:
        correcta = False

    msgs = correccion(
        ev.pregunta,
        ev.tipo,
        ev.respuesta_correcta,
        respuesta,
        ev.nivel.meta.idioma_objetivo,
    )
    try:
        feedback = chat_json(msgs)
    except Exception:
        feedback = {
            "explicacion": "Respuesta correcta: " + ev.respuesta_correcta,
            "tipo_error": "concepto",
            "correcta": correcta,
        }
    correcta = bool(feedback.get("correcta", correcta))

    if correcta:
        ruta_idioma = 1.0
        ruta_tema = 1.0
    else:
        ruta_idioma = 0.0
        ruta_tema = 0.0

    ev.respuesta_usuario = respuesta
    ev.correcta = int(correcta)
    ev.ruta_idioma_score = ruta_idioma
    ev.ruta_tema_score = ruta_tema
    db.add(ev)
    db.commit()
    db.refresh(ev)

    return {
        "correcta": correcta,
        "explicacion": feedback.get("explicacion", ""),
        "tipo_error": feedback.get("tipo_error", "concepto"),
        "ruta_idioma_score": ruta_idioma,
        "ruta_tema_score": ruta_tema,
    }


def _match(correcta: str, respuesta: str) -> bool:
    return correcta.strip().lower() == respuesta.strip().lower()


def _cefr(meta) -> str:
    return getattr(meta.usuario, "nivel_cefr", "A1") if meta.usuario else "A1"
