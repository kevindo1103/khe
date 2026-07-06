import logging
import threading
from collections import OrderedDict
from pathlib import Path

from fastapi import HTTPException, Request, status
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


def _enable_wal(dbapi_conn, _connection_record):
    """Enable WAL journal mode on every new SQLite connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


def _register_unicode_lower(dbapi_conn, _connection_record):
    """Override SQLite built-in lower() with Python str.lower() for Unicode (Vietnamese) case-folding.

    SQLite's native lower() only folds ASCII. Without this, .ilike() on Vietnamese
    diacritic characters (e.g. 'Ệ' in 'DANH VIỆT') silently fails to match.
    """
    dbapi_conn.create_function("lower", 1, lambda s: s.lower() if s is not None else None, deterministic=True)


# ── Per-tenant engine cache (LRU, #184) ────────────────────────────────────
# Cached SQLite engines hold a connection pool — and therefore file handles —
# for the lifetime of the process. Unbounded, N active tenants = N persistent
# file handles (the #181 file-handle-leak path). Cap the cache and evict the
# least-recently-used engine (disposing its pool) when full.
_engine_cache: "OrderedDict[str, Engine]" = OrderedDict()
_cache_lock = threading.Lock()

TENANTS_DIR = Path(settings.TENANTS_DIR)
TENANTS_DIR.mkdir(parents=True, exist_ok=True)


class MasterBase(DeclarativeBase):
    """Base for master.db (tenant registry)."""
    pass


class TenantBase(DeclarativeBase):
    """Base for per-tenant DBs."""
    pass


def _get_tenant_engine(tenant_id: str) -> Engine:
    """Return (and cache) a SQLAlchemy engine for the given tenant slug.

    LRU (#184): on a cache hit the entry is moved to the most-recently-used end.
    On a miss, if the cache is at capacity the least-recently-used engine is
    disposed (releasing its file handle) before the new one is inserted.
    """
    with _cache_lock:
        eng = _engine_cache.get(tenant_id)
        if eng is not None:
            _engine_cache.move_to_end(tenant_id)
            return eng

        # Evict LRU entries until there is room for one more.
        while _engine_cache and len(_engine_cache) >= settings.TENANT_ENGINE_CACHE_SIZE:
            evicted_id, evicted_eng = _engine_cache.popitem(last=False)
            evicted_eng.dispose()
            logger.info("Evicted tenant engine from cache (LRU): %s", evicted_id)

        db_path = TENANTS_DIR / f"{tenant_id}.db"
        eng = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        event.listen(eng, "connect", _enable_wal)
        event.listen(eng, "connect", _register_unicode_lower)
        _engine_cache[tenant_id] = eng
        return eng


def get_tenant_session(tenant_id: str) -> Session:
    """Return a plain (non-generator) DB session for a tenant. Caller must close."""
    return sessionmaker(
        autocommit=False, autoflush=False,
        bind=_get_tenant_engine(tenant_id),
    )()


def get_db(request: Request = None):
    """FastAPI dependency — returns a tenant-scoped DB session."""
    tenant_id = getattr(request.state, "tenant_id", None) if request is not None else None
    if tenant_id is None:
        if settings.ENVIRONMENT == "development":
            tenant_id = settings.DEFAULT_TENANT_ID
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tenant context missing — ensure get_current_user is declared before get_db",
            )
    db = sessionmaker(
        autocommit=False, autoflush=False,
        bind=_get_tenant_engine(tenant_id),
    )()
    try:
        yield db
    finally:
        db.close()


# ── Master DB (tenant registry) ───────────────────────────────────────────
master_engine = create_engine(
    settings.MASTER_DB_URL,
    connect_args={"check_same_thread": False},
)
event.listen(master_engine, "connect", _enable_wal)
MasterSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=master_engine)


def get_master_db():
    """FastAPI dependency — returns a session on the master (tenant registry) DB."""
    db = MasterSessionLocal()
    try:
        yield db
    finally:
        db.close()


_BACKEND_DIR = Path(__file__).resolve().parents[2]


def _upgrade_master_alembic() -> None:
    """Programmatically run alembic upgrade for the master DB.

    Migrations are idempotent, so this safely upgrades legacy master.db files
    that were bootstrapped via create_all() without an alembic_version stamp.
    """
    import alembic.config
    from alembic import command
    from sqlalchemy import create_engine, inspect

    from app.core.config import settings

    db_url = settings.MASTER_DB_URL
    db_path = Path(db_url.replace("sqlite:///", ""))

    # Baseline stamp: if DB has tables but no alembic_version, stamp 001
    if db_path.exists():
        tmp_engine = create_engine(db_url, connect_args={"check_same_thread": False})
        inspector = inspect(tmp_engine)
        table_names = inspector.get_table_names()
        tmp_engine.dispose()

        if table_names and "alembic_version" not in table_names:
            cfg = alembic.config.Config(str(_BACKEND_DIR / "alembic.ini"))
            cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
            cfg.set_main_option("sqlalchemy.url", db_url)
            command.stamp(cfg, "001")
            print("  [alembic] master.db baseline-stamped 001")

    cfg = alembic.config.Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")


def init_master_db():
    """Create / upgrade master tables via Alembic (not create_all)."""
    _upgrade_master_alembic()


def _upgrade_tenant_alembic(tenant_id: str) -> None:
    """Programmatically run alembic upgrade for a single tenant DB."""
    import alembic.config
    from alembic import command
    from sqlalchemy import create_engine, inspect

    db_path = TENANTS_DIR / f"{tenant_id}.db"
    db_url = f"sqlite:///{db_path}"

    # Baseline stamp: if DB has tables but no alembic_version, stamp tenant_001
    if db_path.exists():
        tmp_engine = create_engine(db_url, connect_args={"check_same_thread": False})
        inspector = inspect(tmp_engine)
        table_names = inspector.get_table_names()
        tmp_engine.dispose()

        if table_names and "alembic_version" not in table_names:
            cfg = alembic.config.Config(str(_BACKEND_DIR / "alembic_tenant.ini"))
            cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic_tenant"))
            cfg.set_main_option("sqlalchemy.url", db_url)
            command.stamp(cfg, "tenant_001")
            print(f"  [alembic] {tenant_id} baseline-stamped tenant_001")

    cfg = alembic.config.Config(str(_BACKEND_DIR / "alembic_tenant.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic_tenant"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")


def init_tenant_db(tenant_id: str):
    """Create / upgrade per-tenant tables via Alembic (not create_all)."""
    _upgrade_tenant_alembic(tenant_id)
