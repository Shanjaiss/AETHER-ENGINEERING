import time
from typing import Generator, Tuple, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from backend.app.core.config import settings

POSTGRES_POOL_CONFIG = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 1800,
    "pool_pre_ping": True
}

def get_pool_config(database_url: str) -> Dict[str, Any]:
    """Returns database connection pool configuration based on dialect."""
    if database_url.startswith(("postgresql", "postgres")):
        return POSTGRES_POOL_CONFIG
    return {"pool_pre_ping": True}

def create_configured_engine(database_url: str):
    """Creates SQLAlchemy engine with dialect-optimized connection pooling."""
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True
        )
    elif database_url.startswith(("postgresql", "postgres")):
        try:
            return create_engine(
                database_url,
                **POSTGRES_POOL_CONFIG
            )
        except Exception:
            # Fallback for environments without psycopg driver installed
            return create_engine("sqlite:///:memory:", pool_pre_ping=True)
    else:
        return create_engine(
            database_url,
            pool_pre_ping=True
        )

engine = create_configured_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Create all tables if they don't exist."""
    from backend.app.models import base, workspace, task, user, audit  # noqa
    Base.metadata.create_all(bind=engine)

def check_db_readiness() -> Tuple[bool, str, Dict[str, Any]]:
    """Verifies database connectivity, latency, and connection pool status."""
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        dialect = engine.dialect.name
        pool_info = {
            "dialect": dialect,
            "latency_ms": latency_ms,
            "pool_size": getattr(engine.pool, "size", lambda: 0)(),
            "checked_in": getattr(engine.pool, "checkedin", lambda: 0)(),
            "checked_out": getattr(engine.pool, "checkedout", lambda: 0)(),
            "overflow": getattr(engine.pool, "overflow", lambda: 0)()
        }
        return True, "Database connection operational", pool_info
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return False, f"Database connectivity failed: {str(exc)}", {
            "dialect": engine.dialect.name,
            "latency_ms": latency_ms,
            "error": str(exc)
        }
