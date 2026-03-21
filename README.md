# 3DLiverTumorSegmentation

本项目用于 3D 肝脏/肿瘤分割，并提供 FastAPI 服务，支持同步预测与异步任务处理。

## 0) 项目结构（最新）

当前仓库关键目录如下：

- `APP/`：后端 FastAPI 应用
  - `APP/main.py`：应用入口与路由注册
  - `APP/router/`：接口路由模块（`auth.py`、`predict.py`、`job.py`、`health.py`）
  - `APP/service/`：业务服务层（`auth_service.py`、`inference_service.py`）
  - `APP/persistence/`：数据库层（`db.py`、`crud.py`、`model.py`）
- `Desktop/`：桌面客户端
  - `Desktop/ui/`：界面层（主窗口、登录弹窗、账号中心等）
  - `Desktop/core/`：分割流程控制、API 任务控制与本地 worker
  - `Desktop/infra/`：基础设施工具（`api_client.py`、`path_utils.py`）
  - 说明：UI 常量集中在 `Desktop/ui/ui_text.py` 与 `Desktop/ui/ui_style.py`
- `DataPipeline/`：离线数据处理流水线
  - `DataPipeline/loader/`：数据加载与变换
  - `DataPipeline/processing/`：预处理、扩增、分析脚本
- `Training/`：离线训练与评估
  - `Training/runner/`：`train.py`、`test.py`
  - `Training/core/`：`loss.py`、`evaluate.py`、`log.py`
- `Script/`：启动与测试辅助脚本（`run_all.ps1`、`run_api.ps1`）
- `Doc/`：文档、示例数据、日志、数据库与结果输出

## 1) 一键启动（API + UI）

使用 `Script/run_all.ps1` 在两个终端中分别启动后端 API 与桌面端 UI。

```powershell
powershell -ExecutionPolicy Bypass -File .\Script\run_all.ps1
```

可选参数：

```powershell
# 自定义 API 地址
powershell -ExecutionPolicy Bypass -File .\Script\run_all.ps1 -BaseUrl "http://127.0.0.1:8000"

# 自定义 Python 可执行文件
powershell -ExecutionPolicy Bypass -File .\Script\run_all.ps1 -PythonExe "D:\software\Anaconda\envs\pytorch\python.exe"

# 跳过 /health 等待
powershell -ExecutionPolicy Bypass -File .\Script\run_all.ps1 -SkipHealthCheck
```

启动后的登录流程：

1. 先弹出登录/注册窗口。
2. 如需首次使用，先调用 `/register` 注册，再调用 `/login` 登录。
3. 登录成功后进入主界面。
4. 打开 `账号 -> 账号中心` 查看当前账号与密码。
5. `账号中心` 会自动刷新近期任务，并支持一键复制账号/密码。

停止服务：

- 在两个终端窗口（`LiverSeg API` 与 `LiverSeg UI`）分别按 `Ctrl + C`。

### UI 截图

![UI Main](Doc/img/ui-main.png)

## 2) 端到端流程（演示/面试）

```mermaid
flowchart LR
  A["启动 Script/run_all.ps1"] --> B["登录/注册窗口"]
  B --> C["主界面"]
  C --> D["加载 CT 文件"]
  D --> E["点击 API 分割"]
  E --> F["POST /me/jobs"]
  F --> G["轮询 GET /jobs/{job_id}"]
  G --> H["状态 = succeeded"]
  H --> I["UI 展示分割结果"]
  C --> J["打开账号中心"]
  J --> K["自动刷新 GET /me/jobs"]
```

建议用于简历/作品集的截图：

- `Doc/img/ui-main.png`（主分割界面）
- 登录窗口（进入主界面前）
- 账号中心（账号信息 + 近期任务）

## 3) 本地运行 API

```powershell
conda activate pytorch
python -m pip install -r requirements.txt
python api.py
```

默认服务地址：`http://127.0.0.1:8000`

默认数据库：SQLite（通过 `DB_PATH` 指向 `./Doc/job.db`）。

`Doc` 目录结构：

- `Doc/job.db`：用户/任务数据库
- `Doc/result/`：所有分割输出（本地 + API）
- `Doc/upload/`：API 任务上传的 CT 文件
- `Doc/log/`：API 标准输出与错误日志
- `Doc/report/`：离线实验/分析文本报告

启动前设置 `DB_URL` 可切换到 MySQL：

```powershell
$env:DB_URL = "mysql+pymysql://root:your_password@127.0.0.1:3306/liver_seg?charset=utf8mb4"
python api.py
```

## 4) 主要接口

- `GET /health`
- `POST /register`（账号/密码）
- `POST /login`（账号/密码）
- `POST /predict`（上传文件，同步推理）
- `POST /predict_by_path`（本地路径，同步推理）
- `POST /jobs`（上传文件，异步任务）
- `GET /jobs/{job_id}`（查询异步任务状态）
- `POST /me/jobs`（Basic 认证，创建当前用户异步任务）
- `GET /me/jobs`（Basic 认证，查询当前用户任务列表）

说明：

- 若同时设置 `DB_URL` 与 `DB_PATH`，优先使用 `DB_URL`。
- 也支持 `mysql://...`，会自动转换为 `mysql+pymysql://...`。

### API 辅助脚本

统一脚本（推荐）：

```powershell
# 同步预测
powershell -ExecutionPolicy Bypass -File .\Script\run_api.ps1 -Mode predict

# 异步任务（详细输出）
powershell -ExecutionPolicy Bypass -File .\Script\run_api.ps1 -Mode job

# 异步任务（简洁输出）
powershell -ExecutionPolicy Bypass -File .\Script\run_api.ps1 -Mode job_simple
```

## 5) Docker 部署

### 构建镜像

```powershell
docker build -f Dockerfile -t liver-seg-api:latest .
```

### 使用 docker run 运行

模型权重未包含在仓库中，请将本地模型目录挂载到容器内 `/app/Model/checkpoint`。

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

说明：当 API 在 Docker 中运行时，返回路径如 `/app/Doc/...` 是容器路径。`Script/run_api.ps1` 会尝试自动映射到当前本地目录。

### 使用 docker compose 运行（推荐）

```powershell
docker compose up -d
```

查看日志：

```powershell
docker compose logs -f api
```

停止并移除：

```powershell
docker compose down
```

## 6) 测试与 CI

本地运行 API 逻辑测试：

```powershell
python -m pip install -r requirements.txt
python -m pytest -q test_api.py
```

GitHub Actions 工作流 `API Tests` 会在 push/PR 时自动执行。

## 7) 离线训练与数据处理脚本

训练、评估与数据处理脚本主要分布在：

- `Training/runner/train.py`
- `Training/runner/test.py`
- `Training/core/loss.py`
- `Training/core/evaluate.py`
- `Training/core/log.py`
- `DataPipeline/loader/dataset_train.py`
- `DataPipeline/loader/dataset_test.py`
- `DataPipeline/loader/transform.py`
- `DataPipeline/processing/preprocess.py`
- `DataPipeline/processing/expand.py`
- `DataPipeline/processing/analyze.py`

可通过模块方式运行：

```powershell
python -m Training.runner.train
python -m Training.runner.test
python -m DataPipeline.loader.dataset_train
python -m DataPipeline.processing.preprocess
```
