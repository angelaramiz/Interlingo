from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from pathlib import Path
import json as jsonlib

from .database import Base, engine, get_db
from .models import AppVersion, Evaluacion, Meta, Nivel, Usuario
from .schemas import (
    AppVersionResponse,
    DiagnosticoRespuestas,
    DiagnosticoResultado,
    EvaluacionResultado,
    EvaluacionSubmit,
    Leccion,
    MetaCreate,
    Plan,
)
from .services.adjust import ajustar_nivel
from .services.diagnostic import (
    generar_diagnostico,
    interpretar_meta,
    procesar_diagnostico,
)
from .services.evaluate import calificar, generar_evaluacion
from .services.lesson import generar_leccion
from .services.planner import generar_plan, listar_niveles

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interlingo API", version="0.1.0")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/app-version", response_model=AppVersionResponse)
def app_version(app: str = Query(default=""), db: Session = Depends(get_db)):
    key = f"app_version_{app}" if app else "app_version"
    version_file = Path(__file__).resolve().parent.parent / "static" / "version.json"
    if version_file.is_file():
        try:
            return AppVersionResponse(**jsonlib.loads(version_file.read_text(encoding="utf-8")))
        except (ValueError, TypeError):
            pass
    row = db.get(AppVersion, key)
    if row and row.valor:
        return AppVersionResponse(**row.valor)
    return AppVersionResponse()


@app.get("/api/debug-version")
def debug_version():
    import sys

    base = Path(__file__).resolve().parent.parent
    vf = base / "static" / "version.json"
    info = {
        "python": sys.version.split()[0],
        "cwd": str(Path.cwd()),
        "base": str(base),
        "version_file": str(vf),
        "exists": vf.is_file(),
        "static_dir": sorted(p.name for p in (base / "static").iterdir()) if (base / "static").is_dir() else None,
    }
    if vf.is_file():
        try:
            info["content"] = vf.read_text(encoding="utf-8")[:300]
        except OSError as e:
            info["read_error"] = str(e)
    return info


@app.post("/api/meta")
def crear_meta(payload: MetaCreate, db: Session = Depends(get_db)):
    usuario = Usuario(idioma_objetivo=payload.idioma_objetivo, idioma_nativo=payload.idioma_nativo)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    meta = Meta(
        usuario_id=usuario.id,
        texto=payload.texto,
        idioma_objetivo=payload.idioma_objetivo,
    )
    db.add(meta)
    db.commit()
    db.refresh(meta)
    data = interpretar_meta(db, meta)
    return {"meta_id": meta.id, "usuario_id": usuario.id, "tema": data["tema"]}


@app.get("/api/diagnostico/{meta_id}", response_model=DiagnosticoResultado)
def diagnostico(meta_id: int, db: Session = Depends(get_db)):
    meta = db.get(Meta, meta_id)
    if not meta:
        raise HTTPException(404, "Meta no encontrada")
    data = generar_diagnostico(db, meta)
    return data


@app.post("/api/diagnostico/{meta_id}/resultado")
def resultado_diagnostico(
    meta_id: int, payload: DiagnosticoRespuestas, db: Session = Depends(get_db)
):
    meta = db.get(Meta, meta_id)
    if not meta:
        raise HTTPException(404, "Meta no encontrada")
    resumen = procesar_diagnostico(db, meta, payload.respuestas)
    plan = generar_plan(db, meta, resumen["resumen"])
    return {"niveles": plan}


@app.get("/api/meta/{meta_id}/niveles")
def niveles(meta_id: int, db: Session = Depends(get_db)):
    return [{"id": n.id, "numero": n.numero, "objetivo": n.objetivo, "estado": n.estado}
            for n in listar_niveles(db, meta_id)]


@app.post("/api/leccion/{nivel_id}", response_model=Leccion)
def leccion(nivel_id: int, db: Session = Depends(get_db)):
    nivel = db.get(Nivel, nivel_id)
    if not nivel:
        raise HTTPException(404, "Nivel no encontrado")
    return generar_leccion(db, nivel)


@app.post("/api/evaluacion/{nivel_id}/generar")
def crear_evaluacion(nivel_id: int, db: Session = Depends(get_db)):
    nivel = db.get(Nivel, nivel_id)
    if not nivel:
        raise HTTPException(404, "Nivel no encontrado")
    return generar_evaluacion(db, nivel)


@app.post("/api/evaluacion/{evaluacion_id}/responder", response_model=EvaluacionResultado)
def responder_evaluacion(
    evaluacion_id: int, payload: EvaluacionSubmit, db: Session = Depends(get_db)
):
    ev = db.get(Evaluacion, evaluacion_id)
    if not ev:
        raise HTTPException(404, "Evaluación no encontrada")
    resultado = calificar(db, ev, payload.respuesta)
    ajuste = ajustar_nivel(db, ev.nivel, ev.id, resultado)
    return EvaluacionResultado(**resultado, decision=ajuste["decision"])
