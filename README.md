# 3DLiverTumorSegmentation

This project provides 3D liver/tumor segmentation and exposes a FastAPI service
for synchronous prediction and asynchronous jobs.

## 1) One-click start (API + UI)

Use `scripts/run_all.ps1` to start backend API and desktop UI in two terminals.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1
```

Optional parameters:

```powershell
# custom API address
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -BaseUrl "http://127.0.0.1:8000"

# custom python executable
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -PythonExe "D:\software\Anaconda\envs\pytorch\python.exe"

# skip waiting for /health
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -SkipHealthCheck
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

![UI Main](docs/images/ui-main.png)

## 2) End-to-end flow (for demo/interview)

```mermaid
flowchart LR
  A["Start scripts/run_all.ps1"] --> B["Login/Register dialog"]
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

- `docs/images/ui-main.png` (main segmentation UI)
- login dialog (before entering main UI)
- account center (shows username/password + recent jobs)

## 3) Run API locally

```powershell
conda activate pytorch
python -m pip install -r requirements.txt
python api_min.py
```

Default service address: `http://127.0.0.1:8000`

Default database: SQLite (`./Result/jobs.db` via `DB_PATH`).

Use MySQL by setting `DB_URL` before startup:

```powershell
$env:DB_URL = "mysql+pymysql://root:your_password@127.0.0.1:3306/liver_seg?charset=utf8mb4"
python api_min.py
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
powershell -ExecutionPolicy Bypass -File .\scripts\run_api.ps1 -Mode predict

# async job (verbose)
powershell -ExecutionPolicy Bypass -File .\scripts\run_api.ps1 -Mode job

# async job (concise)
powershell -ExecutionPolicy Bypass -File .\scripts\run_api.ps1 -Mode job_simple
```

## 5) Docker deployment

### Build image

```powershell
docker build -t liver-seg-api:latest .
```

### Run with docker run

Model weights are not included in git. Mount your local model folder to
`/app/Model/model` in the container.

```powershell
docker run --rm -p 8000:8000 `
  -e MODEL_PATH=/app/Model/model/best_model.pth `
  -e RESULT_DIR=/app/Result/api_result `
  -e UPLOAD_DIR=/app/Result/uploads `
  -e DB_PATH=/app/Result/jobs.db `
  -v D:/your_model_dir:/app/Model/model `
  -v D:/your_result_dir:/app/Result `
  liver-seg-api:latest
```

Note: when API runs inside Docker, returned paths like `/app/Result/...` are
container paths. `scripts/run_api.ps1` will try to map `/app/...` to current local
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
python -m pytest -q tests/test_api_min.py
```

GitHub Actions workflow `API Tests` runs automatically on push/PR.

## 7) Offline ML scripts

Training/evaluation/preprocessing scripts are organized under `ml/`:

- `ml/train.py`
- `ml/test.py`
- `ml/preprocess.py`

Run them via module entrypoints:

```powershell
python -m ml.train
python -m ml.test
python -m ml.preprocess
```
