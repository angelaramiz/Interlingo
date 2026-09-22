from sqlalchemy.orm import Session

from ..ai.inference import chat_json
from ..ai.prompts import plan
from ..models import Nivel


def generar_plan(db: Session, meta, diag_resumen: str) -> list[dict]:
    msgs = plan(
        meta.tema,
        [meta.tema],
        meta.idioma_objetivo,
        diag_resumen,
    )
    data = chat_json(msgs)
    for nv in data.get("niveles", []):
        nivel = Nivel(
            meta_id=meta.id,
            numero=nv["numero"],
            objetivo=nv["objetivo"],
            tipo_actividad=nv.get("tipo_actividad", ""),
            criterio_exito=nv.get("criterio_exito", ""),
            estado="pendiente",
        )
        db.add(nivel)
    meta.estado = "aprendizaje"
    db.add(meta)
    db.commit()

    filas = (
        db.query(Nivel)
        .filter(Nivel.meta_id == meta.id)
        .order_by(Nivel.numero)
        .all()
    )
    return [
        {
            "id": n.id,
            "numero": n.numero,
            "objetivo": n.objetivo,
            "tipo_actividad": n.tipo_actividad,
            "criterio_exito": n.criterio_exito,
            "estado": n.estado,
        }
        for n in filas
    ]


def listar_niveles(db: Session, meta_id: int) -> list[Nivel]:
    return (
        db.query(Nivel)
        .filter(Nivel.meta_id == meta_id)
        .order_by(Nivel.numero)
        .all()
    )
