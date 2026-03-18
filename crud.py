import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Job, User


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _job_to_dict(job: Job) -> dict:
    return {
        "job_id": job.job_id,
        "user_id": job.user_id,
        "status": job.status,
        "input_file": job.input_file,
        "original_filename": job.original_filename,
        "result_path": job.result_path,
        "elapsed_ms": job.elapsed_ms,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
    }


def get_user_by_username(session: Session, username: str) -> Optional[dict]:
    stmt = select(User).where(User.username == username)
    user = session.execute(stmt).scalar_one_or_none()
    if user is None:
        return None
    return _user_to_dict(user)


def get_user_entity_by_username(session: Session, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    return session.execute(stmt).scalar_one_or_none()


def create_user(session: Session, username: str, password_hash: str) -> dict:
    now = _utc_now()
    user = User(
        username=username,
        password_hash=password_hash,
        created_at=now,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_to_dict(user)


def create_job(
    session: Session,
    job_id: str,
    input_file: str,
    original_filename: str,
    user_id: Optional[int] = None,
) -> dict:
    now = _utc_now()
    job = Job(
        job_id=job_id,
        user_id=user_id,
        status="pending",
        input_file=input_file,
        original_filename=original_filename,
        result_path=None,
        elapsed_ms=None,
        error=None,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return _job_to_dict(job)


def update_job(
    session: Session,
    job_id: str,
    status: str,
    result_path: Optional[str] = None,
    elapsed_ms: Optional[int] = None,
    error: Optional[str] = None,
) -> Optional[dict]:
    job = session.get(Job, job_id)
    if job is None:
        return None

    job.status = status
    job.result_path = result_path
    job.elapsed_ms = elapsed_ms
    job.error = error
    job.updated_at = _utc_now()
    session.commit()
    session.refresh(job)
    return _job_to_dict(job)


def get_job(session: Session, job_id: str) -> Optional[dict]:
    job = session.get(Job, job_id)
    if job is None:
        return None
    return _job_to_dict(job)


def list_jobs(session: Session, user_id: Optional[int] = None, limit: int = 20) -> list[dict]:
    stmt = select(Job)
    if user_id is not None:
        stmt = stmt.where(Job.user_id == user_id)
    stmt = stmt.order_by(Job.created_at.desc()).limit(limit)
    jobs = session.execute(stmt).scalars().all()
    return [_job_to_dict(job) for job in jobs]
