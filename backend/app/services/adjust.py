import json

from sqlalchemy.orm import Session

from ..ai.inference import chat_json
from ..ai.prompts import ajuste
from ..models import Nivel, Traza


def ajustar_nivel(
    db: Session,
    nivel: Nivel,
    evaluacion_id: int,
    resultado: dict,
) -> dict:
    meta = nivel.meta
    historial = _historial(db, meta.id)
    msgs = ajuste(
        json.dumps(resultado),
        resultado.get("ruta_idioma_score", 0.0),
        resultado.get("ruta_tema_score", 0.0),
        historial,
    )
    try:
        data = chat_json(msgs)
    except Exception:
        data = {"decision": "repetir", "justificacion": "fallo detectado", "nivel_cefr_ajustado": "A1"}

    decision = data.get("decision", "repetir")

    traza = Traza(
        meta_id=meta.id,
        evaluacion_id=evaluacion_id,
        tipo_error=resultado.get("tipo_error", "concepto"),
        detalle=data.get("justificacion", ""),
        decision=decision,
    )
    db.add(traza)

    if decision in ("avanzar", "profundizar"):
        nivel.estado = "completado"
        _siguiente = (
            db.query(Nivel)
            .filter(Nivel.meta_id == meta.id, Nivel.numero == nivel.numero + 1)
            .first()
        )
        if _siguiente:
            _siguiente.estado = "activo"
            db.add(_siguiente)
        else:
            meta.estado = "completado"
            db.add(meta)
    elif decision == "repetir":
        nivel.estado = "repetir"
    else:
        nivel.estado = "simplificar"

    db.add(nivel)
    db.commit()

    return {
        "decision": decision,
        "justificacion": data.get("justificacion", ""),
        "nivel_cefr_ajustado": data.get("nivel_cefr_ajustado", ""),
        "nivel_estado": nivel.estado,
    }


def _historial(db: Session, meta_id: int) -> str:
    trazas = (
        db.query(Traza)
        .filter(Traza.meta_id == meta_id)
        .order_by(Traza.id.desc())
        .limit(10)
        .all()
    )
    return json.dumps([{"tipo_error": t.tipo_error, "decision": t.decision} for t in trazas])
