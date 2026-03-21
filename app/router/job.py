import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app import state
from app.router.dep import require_user
from app.persistence import crud, db
from app.service import inference_service


router = APIRouter()


def _submit_job(file: UploadFile, user_id=None) -> dict:
    upload_path, original_filename = inference_service.save_upload_file(file)
    job_id = uuid.uuid4().hex
    with db.get_session() as session:
        crud.create_job(session, job_id, upload_path, original_filename, user_id=user_id)
    try:
        state.executor.submit(inference_service.run_job, job_id, upload_path, Path(original_filename).name)
    except Exception:
        inference_service.safe_remove(upload_path)
        raise
    return {"job_id": job_id, "status": "pending"}


@router.post("/jobs")
def create_job(file: UploadFile = File(...)):
    return _submit_job(file)


@router.post("/me/jobs")
def create_my_job(file: UploadFile = File(...), current_user: dict = Depends(require_user)):
    return _submit_job(file, user_id=current_user["id"])


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    with db.get_session() as session:
        job = crud.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.get("/me/jobs")
def list_my_jobs(limit: int = 20, current_user: dict = Depends(require_user)):
    limit = max(1, min(limit, 100))
    with db.get_session() as session:
        items = crud.list_jobs(session, user_id=current_user["id"], limit=limit)
    return {"items": items, "count": len(items)}



