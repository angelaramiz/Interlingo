import logging
import socket
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings

log = logging.getLogger("interlingo.db")


def _ipv4_hostaddr(host: str, port: int) -> str | None:
    """IPv4 del host o None si no hay DNS (Render free no tiene ruta IPv6)."""
    try:
        infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        return infos[0][4][0]
    except OSError:
        return None


def _is_supabase(host: str | None) -> bool:
    return bool(host) and ("supabase.co" in host or "pooler.supabase.com" in host)


def make_engine(database_url: str):
    """SQLite local o Postgres (Supabase) en produccion.

    Supabase exige SSL (`sslmode=require` automatico). El endpoint directo
    es dual-stack y libpq prefiere IPv6 (Render free no lo rutea): se fuerza
    IPv4 via `hostaddr` cuando el DNS lo permite. Si no, usar el pooler de
    Supabase (solo IPv4, puerto 6543) con NullPool (pgbouncer).
    """
    database_url = database_url.strip().strip("\"'")
    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args={"check_same_thread": False})
    # La pass puede traer @ : / ? # (Supabase las genera): el ULTIMO @
    # separa auth/host y el PRIMER : separa user/pass; se re-codifica la pass.
    head, sep, tail = database_url.rpartition("@")
    if sep and "://" in head:
        scheme, _, auth = head.partition("://")
        user, colon, password = auth.partition(":")
        if colon:
            database_url = f"{scheme}://{user}:{quote(password, safe='')}@{tail}"
    parts = urlsplit(database_url)
    if _is_supabase(parts.hostname):
        query = dict(parse_qsl(parts.query))
        query.setdefault("sslmode", "require")
        database_url = urlunsplit(parts._replace(query=urlencode(query)))
        connect_args: dict = {"sslmode": "require"}
        hostaddr = _ipv4_hostaddr(parts.hostname, parts.port or 5432)
        if hostaddr:
            connect_args["hostaddr"] = hostaddr
        if (parts.port or 5432) == 6543:
            log.info("db pooler %s (NullPool)", parts.hostname)
            return create_engine(database_url, connect_args=connect_args,
                                 poolclass=NullPool)
        log.info("db directa %s hostaddr=%s", parts.hostname, hostaddr)
        return create_engine(database_url, connect_args=connect_args,
                             pool_pre_ping=True, pool_recycle=300)
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
