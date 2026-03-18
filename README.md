# 3DLiverTumorSegmentation

This project provides 3D liver/tumor segmentation and exposes a FastAPI service
for synchronous prediction and asynchronous jobs.

## 1) One-click start (API + UI)

Use `run_all.ps1` to start backend API and desktop UI in two terminals.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1
```

Optional parameters:

```powershell
# custom API address
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -BaseUrl "http://127.0.0.1:8000"

# custom python executable
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -PythonExe "D:\software\Anaconda\envs\pytorch\python.exe"

# skip waiting for /health
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -SkipHealthCheck
```

Stop services:

- press `Ctrl + C` in each terminal window (`LiverSeg API` and `LiverSeg UI`)

### UI screenshot

![UI Main](docs/images/ui-main.png)

## 2) Run API locally

```powershell
conda activate pytorch
python -m pip install -r requirements-api.txt
python api_min.py
```

Default service address: `http://127.0.0.1:8000`

## 3) Main endpoints

- `GET /health`
- `POST /predict` (upload file, sync inference)
- `POST /predict_by_path` (local path, sync inference)
- `POST /jobs` (upload file, async job)
- `GET /jobs/{job_id}` (query async job status)

More API details: [README_api.md](README_api.md)

## 4) Docker deployment

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

## 5) Tests and CI

Run local API logic tests:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/test_api_min.py
```

GitHub Actions workflow `API Tests` runs automatically on push/PR.
