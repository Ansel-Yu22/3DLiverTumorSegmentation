import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


DB_PATH = "./Doc/job.db"
Base = declarative_base()

engine = None
SessionLocal = None


def _sqlite_url(db_path: str) -> str:
    return f"sqlite:///{Path(db_path).as_posix()}"


def _normalize_db_url(db_url: str) -> str:
    db_url = db_url.strip()
    if db_url.startswith("mysql://"):
        # SQLAlchemy 2.x requires explicit DBAPI driver.
        return db_url.replace("mysql://", "mysql+pymysql://", 1)
    return db_url


def configure_database(db_path: Optional[str] = None, db_url: Optional[str] = None) -> None:
    global DB_PATH, engine, SessionLocal
    connect_args = {}

    if db_url:
        database_url = _normalize_db_url(db_url)
    else:
        DB_PATH = db_path or DB_PATH
        db_parent = Path(DB_PATH).parent
        if str(db_parent) not in {"", "."}:
            os.makedirs(db_parent, exist_ok=True)
        database_url = _sqlite_url(DB_PATH)

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def init_db(db_path: Optional[str] = None, db_url: Optional[str] = None) -> None:
    if db_path is not None or db_url is not None or engine is None or SessionLocal is None:
        configure_database(db_path=db_path or DB_PATH, db_url=db_url)

    from APP.persistence import models  # noqa: F401

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
        env_db_url = os.getenv("DB_URL", "").strip()
        configure_database(db_path=DB_PATH if not env_db_url else None, db_url=env_db_url or None)
    return SessionLocal()
