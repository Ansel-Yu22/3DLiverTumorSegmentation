import os
from typing import Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()

engine = None
SessionLocal = None


def _normalize_db_url(db_url: str) -> str:
    value = (db_url or "").strip()
    if value.startswith("mysql://"):
        # SQLAlchemy 2.x requires explicit DBAPI driver.
        return value.replace("mysql://", "mysql+pymysql://", 1)
    return value


def _resolve_mysql_url(db_url: Optional[str] = None) -> str:
    value = _normalize_db_url(db_url if db_url is not None else os.getenv("DB_URL", ""))
    if not value:
        raise RuntimeError("DB_URL is required. This project only supports MySQL.")
    if not value.startswith("mysql+pymysql://"):
        raise RuntimeError(
            "Invalid DB_URL. Only MySQL is supported. Use mysql+pymysql://... (mysql://... is also accepted)."
        )
    return value


def configure_database(db_url: Optional[str] = None) -> None:
    global engine, SessionLocal
    database_url = _resolve_mysql_url(db_url)
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def init_db(db_url: Optional[str] = None) -> None:
    if db_url is not None or engine is None or SessionLocal is None:
        configure_database(db_url=db_url)

    from app.persistence import model  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_legacy_columns()


def _ensure_legacy_columns() -> None:
    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("jobs")}
    if "user_id" in columns:
        return

    add_sql = "ALTER TABLE jobs ADD COLUMN user_id INTEGER NULL"
    if engine.dialect.name == "mysql":
        add_sql = "ALTER TABLE jobs ADD COLUMN user_id INT NULL"

    with engine.begin() as conn:
        conn.execute(text(add_sql))


def get_session():
    if SessionLocal is None:
        configure_database()
    return SessionLocal()

