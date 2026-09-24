"""Sesiones persistidas en backend: GET /api/metas lista sesiones guardadas.

Usa SQLite en memoria + chat_json mockeado (sin clave ni modelo real).
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
import app.services.diagnostic as diagnostic

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def _override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db

client = TestClient(app)

diagnostic.chat_json = lambda msgs: {"tema": "ETL", "conceptos": ["extraccion"]}


def _crear_meta(texto="quiero aprender ETL en ingles"):
    r = client.post("/api/meta", json={"texto": texto, "idioma_objetivo": "en"})
    assert r.status_code == 200, r.text
    return r.json()


def test_metas_lista_vacia_al_inicio():
    r = client.get("/api/metas")
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_meta_creada_aparece_en_lista():
    meta = _crear_meta()
    r = client.get("/api/metas")
    assert r.status_code == 200
    items = r.json()
    ids = [m["id"] for m in items]
    assert meta["meta_id"] in ids
    item = next(m for m in items if m["id"] == meta["meta_id"])
    assert item["tema"] == "ETL"
    assert item["idioma_objetivo"] == "en"
    assert item["estado"] == "diagnostico"
    assert "texto" in item


def test_metas_respeta_limite():
    _crear_meta("meta extra 1")
    _crear_meta("meta extra 2")
    r = client.get("/api/metas?limit=1")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_metas_orden_recientes_primero():
    a = _crear_meta("primera sesion")
    b = _crear_meta("segunda sesion")
    r = client.get("/api/metas?limit=50")
    ids = [m["id"] for m in r.json()]
    assert ids.index(b["meta_id"]) < ids.index(a["meta_id"])


def test_meta_fallida_no_deja_zombie(monkeypatch):
    def _boom(msgs):
        raise RuntimeError("openrouter 401")
    monkeypatch.setattr(diagnostic, "chat_json", _boom)
    no_raise = TestClient(app, raise_server_exceptions=False)
    r = no_raise.post("/api/meta", json={"texto": "sesion que falla", "idioma_objetivo": "en"})
    assert r.status_code == 500
    items = client.get("/api/metas?limit=50").json()
    assert all(m["texto"] != "sesion que falla" for m in items)
