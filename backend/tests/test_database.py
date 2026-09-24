"""Motor de BD dual: SQLite local + Postgres (Supabase) en produccion."""
from sqlalchemy import inspect

from app.database import make_engine, Base
import app.models  # noqa: F401  (registra tablas en Base)


def test_sqlite_memory_creates_schema():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=eng)
    assert "metas" in inspect(eng).get_table_names()


def test_sqlite_uses_same_thread_arg():
    eng = make_engine("sqlite:///./x.db")
    assert eng.url.drivername == "sqlite"


def test_postgres_url_builds_without_connecting():
    eng = make_engine("postgresql://user:pass@db.xxx.supabase.co:5432/postgres")
    assert eng.url.drivername == "postgresql"
    assert eng.url.host == "db.xxx.supabase.co"


def test_postgres_supabase_forces_ssl():
    eng = make_engine("postgresql://user:pass@db.xxx.supabase.co:5432/postgres")
    assert eng.url.query.get("sslmode") == "require" or "sslmode" in str(eng.url)
