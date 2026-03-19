# Release Notes - v0.2.0

Release date: 2026-03-19

## Highlights

- Added FastAPI-based segmentation service with synchronous and asynchronous inference APIs.
- Added async job workflow: submit job, poll status, return result path, elapsed time, and error message.
- Introduced SQLite + SQLAlchemy job persistence (`db.py`, `models.py`, `crud.py`).
- Added API test suite and GitHub Actions CI for automated API validation.
- Added Docker and Docker Compose deployment support for backend service.
- Integrated API inference into desktop UI with a dedicated `API分割` action.
- Added `run_all.ps1` one-click launcher for API + UI startup.
- Updated README with one-click startup guide and UI screenshot.

## API Endpoints

- `GET /health`
- `POST /predict`
- `POST /predict_by_path`
- `POST /jobs`
- `GET /jobs/{job_id}`

## Developer Experience

- API paths configurable via environment variables (`MODEL_PATH`, `RESULT_DIR`, `UPLOAD_DIR`, `DB_PATH`).
- Added clear local scripts for sync/async API verification (`run_predict.ps1`, `run_job.ps1`, `run_job_simple.ps1`).
- Improved project onboarding with deployment and test documentation.

## Resume/Interview Value

- Demonstrates end-to-end Python backend engineering: model serving, async task orchestration, persistence layer, CI, containerization, and desktop integration.
- Shows practical software delivery workflow: incremental refactor, automated tests, reproducible startup scripts, and release versioning.
