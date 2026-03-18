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

## 3) Endpoints

- `GET /health`
  - health check
- `POST /predict`
  - upload file and run sync prediction
- `POST /predict_by_path`
  - run sync prediction by local path
- `POST /jobs`
  - upload file and create async job
- `GET /jobs/{job_id}`
  - poll async job status

## 4) PowerShell helpers

- Sync predict helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_predict.ps1
```

- Async job helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_job.ps1
```

- Concise async helper (with failure reason and timing):

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
