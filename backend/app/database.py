from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings


def make_engine(database_url: str):
    """SQLite local o Postgres (Supabase) en produccion.

    Supabase exige SSL: si el host es *.supabase.co y la URL no trae
    sslmode, se agrega `sslmode=require` automaticamente.
    """
    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args={"check_same_thread": False})
    parts = urlsplit(database_url)
    if parts.hostname and parts.hostname.endswith("supabase.co"):
        query = dict(parse_qsl(parts.query))
        query.setdefault("sslmode", "require")
        database_url = urlunsplit(parts._replace(query=urlencode(query)))
    return create_engine(database_url, pool_pre_ping=True)


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
