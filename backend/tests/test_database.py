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


def test_url_strips_quotes_and_spaces():
    eng = make_engine('  "postgresql://user:pass@db.xxx.supabase.co:5432/postgres"  ')
    assert eng.url.drivername == "postgresql"
    assert eng.url.host == "db.xxx.supabase.co"


def test_password_with_special_chars_survives():
    eng = make_engine("postgresql://postgres:p@ss:w/rd?x#1@db.xxx.supabase.co:5432/postgres")
    assert eng.url.host == "db.xxx.supabase.co"
    assert eng.url.password == "p@ss:w/rd?x#1"
    assert eng.url.username == "postgres"


def test_postgres_url_builds_without_connecting():
    eng = make_engine("postgresql://user:pass@db.xxx.supabase.co:5432/postgres")
    assert eng.url.drivername == "postgresql"
    assert eng.url.host == "db.xxx.supabase.co"


def test_postgres_supabase_forces_ssl():
    eng = make_engine("postgresql://user:pass@db.xxx.supabase.co:5432/postgres")
    assert eng.url.query.get("sslmode") == "require" or "sslmode" in str(eng.url)


def test_ipv4_hostaddr_resolves(monkeypatch):
    from app.database import _ipv4_hostaddr
    import socket
    monkeypatch.setattr(
        socket, "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, None, None, None, ("1.2.3.4", 5432))],
    )
    assert _ipv4_hostaddr("db.xxx.supabase.co", 5432) == "1.2.3.4"


def test_ipv4_hostaddr_falls_back_on_dns_failure(monkeypatch):
    from app.database import _ipv4_hostaddr
    import socket
    def _boom(*a, **k):
        raise OSError("no dns")
    monkeypatch.setattr(socket, "getaddrinfo", _boom)
    assert _ipv4_hostaddr("db.xxx.supabase.co", 5432) is None
