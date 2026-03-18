import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DB_PATH = "./Result/jobs.db"
Base = declarative_base()

engine = None
SessionLocal = None


def _sqlite_url(db_path: str) -> str:
    return f"sqlite:///{Path(db_path).as_posix()}"


def configure_database(db_path: str) -> None:
    global DB_PATH, engine, SessionLocal
    DB_PATH = db_path
    db_parent = Path(db_path).parent
    if str(db_parent) not in {"", "."}:
        os.makedirs(db_parent, exist_ok=True)

    engine = create_engine(_sqlite_url(db_path), connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def init_db(db_path: Optional[str] = None) -> None:
    if db_path is not None or engine is None or SessionLocal is None:
        configure_database(db_path or DB_PATH)

    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session():
    if SessionLocal is None:
        configure_database(DB_PATH)
    return SessionLocal()
