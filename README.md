# 3DLiverTumorSegmentation

This project provides 3D liver/tumor segmentation and exposes a FastAPI service
for synchronous prediction and asynchronous jobs.

## 1) One-click start (API + UI)

Use `Script/run_all.ps1` to start backend API and desktop UI in two terminals.

```powershell
powershell -ExecutionPolicy Bypass -File .\Script\run_all.ps1
```

Optional parameters:

```powershell
# custom API address
powershell -ExecutionPolicy Bypass -File .\Script\run_all.ps1 -BaseUrl "http://127.0.0.1:8000"

# custom python executable
powershell -ExecutionPolicy Bypass -File .\Script\run_all.ps1 -PythonExe "D:\software\Anaconda\envs\pytorch\python.exe"

# skip waiting for /health
powershell -ExecutionPolicy Bypass -File .\Script\run_all.ps1 -SkipHealthCheck
```

Login flow after startup:

1. A login/register dialog appears first.
2. Register once (`/register`) if needed, then login (`/login`).
3. After successful login, the main UI opens.
4. Open `账号 -> 账号中心` to view current username/password.
5. `账号中心` auto-refreshes recent jobs and supports one-click copy for username/password.

Stop services:

- press `Ctrl + C` in each terminal window (`LiverSeg API` and `LiverSeg UI`)

### UI screenshot

![UI Main](Doc/img/ui-main.png)

## 2) End-to-end flow (for demo/interview)

```mermaid
flowchart LR
  A["Start Script/run_all.ps1"] --> B["Login/Register dialog"]
  B --> C["Main UI"]
  C --> D["Load CT file"]
  D --> E["Click API segmentation"]
  E --> F["POST /me/jobs"]
  F --> G["Poll GET /jobs/{job_id}"]
  G --> H["Status = succeeded"]
  H --> I["Show segmentation result in UI"]
  C --> J["Open 账号中心"]
  J --> K["Auto-refresh GET /me/jobs"]
```

Recommended screenshots to show in resume/portfolio:

- `Doc/img/ui-main.png` (main segmentation UI)
- login dialog (before entering main UI)
- account center (shows username/password + recent jobs)

## 3) Run API locally

```powershell
conda activate pytorch
python -m pip install -r requirements.txt
python api.py
```

Default service address: `http://127.0.0.1:8000`

Default database: SQLite (`./Doc/job.db` via `DB_PATH`).

Doc directory layout:

- `Doc/job.db`: user/job database
- `Doc/result/`: all segmentation outputs (local + API)
- `Doc/upload/`: uploaded CT files used by API jobs
- `Doc/log/`: API stdout/stderr logs
- `Doc/report/`: offline experiment/analysis text reports

Use MySQL by setting `DB_URL` before startup:

```powershell
$env:DB_URL = "mysql+pymysql://root:your_password@127.0.0.1:3306/liver_seg?charset=utf8mb4"
python api.py
```

## 4) Main endpoints

- `GET /health`
- `POST /register` (username/password)
- `POST /login` (username/password)
- `POST /predict` (upload file, sync inference)
- `POST /predict_by_path` (local path, sync inference)
- `POST /jobs` (upload file, async job)
- `GET /jobs/{job_id}` (query async job status)
- `POST /me/jobs` (Basic auth, create current user's async job)
- `GET /me/jobs` (Basic auth, list current user's jobs)

Notes:

- If `DB_URL` is set, it has higher priority than `DB_PATH`.
- `mysql://...` is also accepted and will be auto-converted to `mysql+pymysql://...`.

### API helper scripts

Unified helper (recommended):

```powershell
# sync predict
powershell -ExecutionPolicy Bypass -File .\Script\run_api.ps1 -Mode predict

# async job (verbose)
powershell -ExecutionPolicy Bypass -File .\Script\run_api.ps1 -Mode job

# async job (concise)
powershell -ExecutionPolicy Bypass -File .\Script\run_api.ps1 -Mode job_simple
```

## 5) Docker deployment

### Build image

```powershell
docker build -f Dockerfile -t liver-seg-api:latest .
```

### Run with docker run

Model weights are not included in git. Mount your local model folder to
`/app/Model/checkpoint` in the container.

```powershell
docker run --rm -p 8000:8000 `
  -e MODEL_PATH=/app/Model/checkpoint/best_model.pth `
  -e RESULT_DIR=/app/Doc/result `
  -e UPLOAD_DIR=/app/Doc/upload `
  -e DB_PATH=/app/Doc/job.db `
  -v D:/your_model_dir:/app/Model/checkpoint `
  -v D:/your_result_dir:/app/Doc `
  liver-seg-api:latest
```

Note: when API runs inside Docker, returned paths like `/app/Doc/...` are
container paths. `Script/run_api.ps1` will try to map `/app/...` to current local
directory automatically.

### Run with docker compose (recommended)

```powershell
docker compose up -d
```

View logs:

```powershell
docker compose logs -f api
```

Stop and remove:

```powershell
docker compose down
```

## 6) Tests and CI

Run local API logic tests:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q test_api.py
```

GitHub Actions workflow `API Tests` runs automatically on push/PR.

## 7) Offline ML scripts

Training/evaluation/preprocessing scripts are organized under `Training/`:

- `Training/runner/train.py`
- `Training/runner/test.py`
- `Training/core/loss.py`
- `Training/core/evaluate.py`
- `Training/core/log.py`
- `DataPipeline/processing/preprocess.py`

Run them via module entrypoints:

```powershell
python -m Training.runner.train
python -m Training.runner.test
python -m DataPipeline.processing.preprocess
```
