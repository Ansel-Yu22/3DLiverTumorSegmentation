# API Quickstart

## 1) Environment
Use your `pytorch` conda env:

```powershell
conda activate pytorch
python -V
```

Install runtime dependencies:

```powershell
python -m pip install -r requirements-api.txt
```

Install development/test dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

## 2) Start API

```powershell
python api_min.py
```

Default address:

- `http://127.0.0.1:8000`

### Switch database to MySQL (optional)

Default DB is SQLite (`./Result/jobs.db`).
To use MySQL, set `DB_URL` before starting API:

```powershell
$env:DB_URL = "mysql+pymysql://root:your_password@127.0.0.1:3306/liver_seg?charset=utf8mb4"
python api_min.py
```

Notes:

- If `DB_URL` is set, it has higher priority than `DB_PATH`.
- `mysql://...` is also accepted and will be auto-converted to `mysql+pymysql://...`.

## 3) Endpoints

- `GET /health`
  - health check
- `POST /register`
  - register user (`username`, `password`)
- `POST /login`
  - login validation (`username`, `password`)
- `POST /predict`
  - upload file and run sync prediction
- `POST /predict_by_path`
  - run sync prediction by local path
- `POST /jobs`
  - upload file and create async job
- `GET /jobs/{job_id}`
  - poll async job status
- `POST /me/jobs` (HTTP Basic auth)
  - create async job for current user
- `GET /me/jobs` (HTTP Basic auth)
  - list current user's jobs

## 4) PowerShell helpers

- Unified helper (recommended):

```powershell
# sync predict
powershell -ExecutionPolicy Bypass -File .\run_api.ps1 -Mode predict

# async job (verbose)
powershell -ExecutionPolicy Bypass -File .\run_api.ps1 -Mode job

# async job (concise)
powershell -ExecutionPolicy Bypass -File .\run_api.ps1 -Mode job_simple
```

Legacy wrappers are still available:

- Sync predict wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_predict.ps1
```

- Async job wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_job.ps1
```

- Concise async wrapper (with failure reason and timing):

```powershell
powershell -ExecutionPolicy Bypass -File .\run_job_simple.ps1
```

## 5) Tests

Run API logic tests:

```powershell
python -m pytest -q tests/test_api_min.py
```

These tests validate API contract and job state transitions. They mock model inference for speed.

## 6) CI

GitHub Actions workflow file:

- `.github/workflows/api-test.yml`

It runs `pytest -q tests/test_api_min.py` on push/PR for API-related files.
