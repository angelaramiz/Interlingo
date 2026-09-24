"""TDD RED — Diccionario integrado (clic en palabra → traducción).

Contrato:
  POST /api/diccionario {palabra, idioma_objetivo, idioma_nativo, contexto}
  -> {termino, traduccion, definicion, ejemplo}

Cubre: prompt, servicio (validación/normalización), ruta HTTP,
edge cases (vacío, nulo, largo, unicode) y errores (IA caída).
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai import prompts
from app.database import Base, get_db
from app.main import app

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


# ---------- Step 1: interfaces / schemas ----------

class TestDiccionarioSchemas:
    def test_request_response_schemas_existen(self):
        from app.schemas import DiccionarioRequest, DiccionarioResponse

        r = DiccionarioRequest(palabra="pipeline")
        assert r.palabra == "pipeline"
        assert r.idioma_objetivo == "en"
        assert r.idioma_nativo == "es"

        resp = DiccionarioResponse(
            termino="pipeline", traduccion="tubería",
            definicion="d", ejemplo="e",
        )
        assert resp.termino == "pipeline"
        assert resp.traduccion == "tubería"

    def test_request_rechaza_palabra_faltante(self):
        from pydantic import ValidationError

        import pytest

        from app.schemas import DiccionarioRequest

        with pytest.raises(ValidationError):
            DiccionarioRequest()  # type: ignore


# ---------- prompt ----------

class TestDiccionarioPrompt:
    def test_prompt_usa_nombres_completos_de_idioma(self):
        msgs = prompts.diccionario("pipeline", "en", "es")
        texto = " ".join(m["content"] for m in msgs)
        assert "English" in texto
        assert "Spanish" in texto
        # nunca códigos sueltos como idioma (el modelo 4B se equivoca si ve "en")
        assert "pipeline" in texto

    def test_prompt_incluye_contexto_y_esquema_json(self):
        msgs = prompts.diccionario("pipeline", "en", "es", contexto="data engineering")
        texto = " ".join(m["content"] for m in msgs)
        assert "data engineering" in texto
        for clave in ("termino", "traduccion", "definicion", "ejemplo"):
            assert clave in texto

    def test_prompt_sin_contexto_no_rompe(self):
        msgs = prompts.diccionario("hola", "es", "en")
        assert isinstance(msgs, list) and len(msgs) == 2


# ---------- servicio ----------

class TestTraducirPalabra:
    def test_happy_path_devuelve_traduccion(self, monkeypatch):
        import app.services.dictionary as dic

        monkeypatch.setattr(
            dic, "chat_json",
            lambda msgs: {
                "termino": "pipeline",
                "traduccion": "tubería",
                "definicion": "conducto de datos",
                "ejemplo": "The pipeline failed.",
            },
        )
        out = dic.traducir_palabra("pipeline", "en", "es")
        assert out["termino"] == "pipeline"
        assert out["traduccion"] == "tubería"
        assert out["definicion"] == "conducto de datos"
        assert out["ejemplo"] == "The pipeline failed."

    def test_normaliza_espacios(self, monkeypatch):
        import app.services.dictionary as dic

        vista = {}
        monkeypatch.setattr(dic, "chat_json", lambda msgs: vista.update(msgs=msgs) or {
            "termino": "pipeline", "traduccion": "tubería"})
        out = dic.traducir_palabra("  pipeline  ")
        assert out["termino"] == "pipeline"

    def test_vacio_lanza_valueerror(self):
        import pytest

        import app.services.dictionary as dic

        with pytest.raises(ValueError):
            dic.traducir_palabra("")
        with pytest.raises(ValueError):
            dic.traducir_palabra("   ")

    def test_none_lanza_valueerror(self):
        import pytest

        import app.services.dictionary as dic

        with pytest.raises(ValueError):
            dic.traducir_palabra(None)  # type: ignore

    def test_palabra_muy_larga_lanza_valueerror(self):
        import pytest

        import app.services.dictionary as dic

        with pytest.raises(ValueError):
            dic.traducir_palabra("x" * 101)

    def test_unicode_y_acentos(self, monkeypatch):
        import app.services.dictionary as dic

        monkeypatch.setattr(
            dic, "chat_json",
            lambda msgs: {"termino": "niño", "traduccion": "child",
                          "definicion": "", "ejemplo": ""},
        )
        out = dic.traducir_palabra("niño")
        assert out["traduccion"] == "child"

    def test_campos_faltantes_tienen_default(self, monkeypatch):
        import app.services.dictionary as dic

        monkeypatch.setattr(dic, "chat_json", lambda msgs: {"traduccion": "tubería"})
        out = dic.traducir_palabra("pipeline")
        assert out["termino"] == "pipeline"
        assert out["definicion"] == ""
        assert out["ejemplo"] == ""

    def test_usa_dispatcher_chat_json(self, monkeypatch):
        # el servicio debe llamar a app.ai.inference.chat_json vía import local,
        # nunca a orcarouter/local directo
        import app.services.dictionary as dic
        import inspect

        src = inspect.getsource(dic)
        assert "chat_json" in src
        assert "from ..ai.inference import chat_json" in src or \
            "from app.ai.inference import chat_json" in src or \
            "from .ai.inference import" in src or "ai.inference" in src


# ---------- ruta HTTP ----------

class TestDiccionarioRoute:
    def test_post_happy_path(self, monkeypatch):
        import app.services.dictionary as dic

        monkeypatch.setattr(
            dic, "chat_json",
            lambda msgs: {"termino": "pipeline", "traduccion": "tubería",
                          "definicion": "conducto", "ejemplo": "ex"},
        )
        r = client.post("/api/diccionario", json={"palabra": "pipeline"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["termino"] == "pipeline"
        assert data["traduccion"] == "tubería"

    def test_post_con_contexto(self, monkeypatch):
        import app.services.dictionary as dic

        monkeypatch.setattr(
            dic, "chat_json",
            lambda msgs: {"termino": "branch", "traduccion": "rama",
                          "definicion": "", "ejemplo": ""},
        )
        r = client.post("/api/diccionario",
                        json={"palabra": "branch", "contexto": "git workflow"})
        assert r.status_code == 200, r.text

    def test_post_vacia_da_400(self):
        r = client.post("/api/diccionario", json={"palabra": "   "})
        assert r.status_code == 400

    def test_post_sin_palabra_da_422(self):
        r = client.post("/api/diccionario", json={})
        assert r.status_code == 422

    def test_post_palabra_larga_da_400(self):
        r = client.post("/api/diccionario", json={"palabra": "x" * 101})
        assert r.status_code == 400

    def test_post_fallo_ia_da_502(self, monkeypatch):
        import app.services.dictionary as dic

        def _boom(msgs):
            raise RuntimeError("ia caída")

        monkeypatch.setattr(dic, "chat_json", _boom)
        r = client.post("/api/diccionario", json={"palabra": "pipeline"})
        assert r.status_code == 502
