import time
from typing import Optional

from sqlalchemy.orm import Session

from models import Job


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _job_to_dict(job: Job) -> dict:
    return {
        "job_id": job.job_id,
        "status": job.status,
        "input_file": job.input_file,
        "original_filename": job.original_filename,
        "result_path": job.result_path,
        "elapsed_ms": job.elapsed_ms,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def create_job(session: Session, job_id: str, input_file: str, original_filename: str) -> dict:
    now = _utc_now()
    job = Job(
        job_id=job_id,
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
