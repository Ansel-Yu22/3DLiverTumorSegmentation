import os
import shutil
import hashlib
import secrets
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import numpy as np
import SimpleITK as sitk
import torch
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from scipy import ndimage
from torch.utils.data import DataLoader, Dataset

import crud
import db
from Model.Model import UNet


MODEL_PATH = os.getenv("MODEL_PATH", "./Model/model/best_model.pth")
RESULT_DIR = os.getenv("RESULT_DIR", "./Result/api_result")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./Result/uploads")
DB_PATH = os.getenv("DB_PATH", "./Result/jobs.db")
DB_URL = os.getenv("DB_URL", "").strip()
N_LABEL = 3
DROP_RATE = 0.3
UPPER = 300
LOWER = -100
XY_DOWN_SCALE = 0.5
Z_DOWN_SCALE = 1.0
TC_SIZE = 80
TC_STRIDE = 20

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
executor = ThreadPoolExecutor(max_workers=1)
security = HTTPBasic()


def _safe_remove(path: Optional[str]) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        # Best-effort cleanup; do not fail request/job flow.
        pass


class PredictRequest(BaseModel):
    ct_path: str


class UserAuthRequest(BaseModel):
    username: str
    password: str


class InferenceDataset(Dataset):
    def __init__(self, ct_path: str):
        self.n_label = N_LABEL
        self.cut_size = TC_SIZE
        self.cut_stride = TC_STRIDE

        self.ct = sitk.ReadImage(ct_path, sitk.sitkInt16)
        self.ct_np = sitk.GetArrayFromImage(self.ct)
        self.ori_shape = self.ct_np.shape

        self.ct_np = ndimage.zoom(
            self.ct_np,
            (Z_DOWN_SCALE, XY_DOWN_SCALE, XY_DOWN_SCALE),
            order=3,
        )

        self.ct_np[self.ct_np > UPPER] = UPPER
        self.ct_np[self.ct_np < LOWER] = LOWER
        self.ct_np = (self.ct_np + 100) / 400
        self.ct_np = self.ct_np.astype(np.float32)

        self.ct_np = self._padding_ct(self.ct_np, self.cut_size, self.cut_stride)
        self.padding_shape = self.ct_np.shape
        self.ct_np = self._extract_ordered_overlap(self.ct_np, self.cut_size, self.cut_stride)
        self.result = None

    def __getitem__(self, index):
        data = torch.from_numpy(self.ct_np[index])
        data = torch.FloatTensor(data).unsqueeze(0)
        return data

    def __len__(self):
        return len(self.ct_np)

    def update_result(self, tensor):
        if self.result is None:
            self.result = tensor
        else:
            self.result = torch.cat((self.result, tensor), dim=0)

    def recompone_result(self):
        patch_s = self.result.shape[2]
        n_patches = (self.padding_shape[0] - patch_s) // self.cut_stride + 1
        full_prob = torch.zeros((self.n_label, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))
        full_sum = torch.zeros((self.n_label, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))

        for s in range(n_patches):
            full_prob[:, s * self.cut_stride : s * self.cut_stride + patch_s] += self.result[s]
            full_sum[:, s * self.cut_stride : s * self.cut_stride + patch_s] += 1

        final_avg = full_prob / full_sum
        ct = final_avg[:, : self.ori_shape[0], : self.ori_shape[1], : self.ori_shape[2]]
        return ct.unsqueeze(0)

    @staticmethod
    def _padding_ct(ct, size, stride):
        ct_s, ct_h, ct_w = ct.shape
        leftover_s = (ct_s - size) % stride
        if leftover_s != 0:
            s = ct_s + (stride - leftover_s)
        else:
            s = ct_s
        tmp_full_imgs = np.zeros((s, ct_h, ct_w), dtype=np.float32)
        tmp_full_imgs[:ct_s] = ct
        return tmp_full_imgs

    @staticmethod
    def _extract_ordered_overlap(ct, size, stride):
        ct_s, ct_h, ct_w = ct.shape
        n_patches = (ct_s - size) // stride + 1
        patches = np.empty((n_patches, size, ct_h, ct_w), dtype=np.float32)
        for s in range(n_patches):
            patch = ct[s * stride : s * stride + size]
            patches[s] = patch
        return patches


def _save_upload_file(file: UploadFile) -> tuple[str, str]:
    suffixes = "".join(Path(file.filename).suffixes)
    suffix = suffixes if suffixes else ".nii"
    upload_name = f"{uuid.uuid4().hex}{suffix}"
    upload_path = os.path.join(UPLOAD_DIR, upload_name)
    try:
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        try:
            file.file.close()
        except Exception:
            pass
    return upload_path, file.filename


def _hash_password(password: str) -> str:
    iterations = 120_000
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iter_text, salt, digest = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_text)
    except Exception:
        return False

    calc = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations).hex()
    return secrets.compare_digest(calc, digest)


def _require_user(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    username = (credentials.username or "").strip()
    password = credentials.password or ""
    with db.get_session() as session:
        user = crud.get_user_entity_by_username(session, username)
    if user is None or not _verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"id": user.id, "username": user.username}


def run_predict(ct_path: str, output_name: Optional[str] = None) -> str:
    dataset = InferenceDataset(ct_path)
    dataloader = DataLoader(dataset=dataset, batch_size=1, num_workers=0, shuffle=False)

    model.eval()
    with torch.no_grad():
        for data in dataloader:
            data = data.to(device)
            output = model(data)
            output = torch.nn.functional.interpolate(
                output,
                scale_factor=(1 / Z_DOWN_SCALE, 1 / XY_DOWN_SCALE, 1 / XY_DOWN_SCALE),
                mode="trilinear",
                align_corners=False,
            )
            dataset.update_result(output.detach().cpu())

    pred = dataset.recompone_result()
    pred = torch.argmax(pred, dim=1)
    pred_np = np.squeeze(pred.numpy(), axis=0).astype(np.uint8)
    pred_img = sitk.GetImageFromArray(pred_np)
    pred_img.SetDirection(dataset.ct.GetDirection())
    pred_img.SetOrigin(dataset.ct.GetOrigin())
    pred_img.SetSpacing(dataset.ct.GetSpacing())

    out_name = output_name if output_name else f"result-{Path(ct_path).name}"
    out_path = os.path.join(RESULT_DIR, out_name)
    sitk.WriteImage(pred_img, out_path)
    return out_path


def _run_job(job_id: str, upload_path: str, original_filename: str) -> None:
    with db.get_session() as session:
        crud.update_job(session, job_id, "running")

    start = time.time()
    try:
        output_name = f"result-{Path(original_filename).name}"
        result_path = run_predict(upload_path, output_name=output_name)
        elapsed_ms = int((time.time() - start) * 1000)
        with db.get_session() as session:
            crud.update_job(session, job_id, "succeeded", result_path=result_path, elapsed_ms=elapsed_ms, error=None)
    except Exception as exc:
        elapsed_ms = int((time.time() - start) * 1000)
        with db.get_session() as session:
            crud.update_job(session, job_id, "failed", result_path=None, elapsed_ms=elapsed_ms, error=str(exc))
    finally:
        _safe_remove(upload_path)


def _load_state_dict(model_path: str):
    try:
        checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    except TypeError:
        checkpoint = torch.load(model_path, map_location=device)

    if isinstance(checkpoint, dict) and "net" in checkpoint:
        state_dict = checkpoint["net"]
    elif isinstance(checkpoint, dict):
        state_dict = checkpoint
    else:
        raise ValueError("Unsupported checkpoint format: expected dict or dict with key 'net'.")

    if any(k.startswith("module.") for k in state_dict.keys()):
        state_dict = {k.replace("module.", "", 1): v for k, v in state_dict.items()}
    return state_dict


def _startup_init() -> None:
    global model
    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    db.init_db(db_path=DB_PATH if not DB_URL else None, db_url=DB_URL or None)
    net = UNet(in_channel=1, out_channel=N_LABEL, drop_rate=DROP_RATE, training=False)
    net = net.to(device)
    state_dict = _load_state_dict(MODEL_PATH)
    net.load_state_dict(state_dict)
    model = net


@asynccontextmanager
async def lifespan(_: FastAPI):
    _startup_init()
    yield


app = FastAPI(title="3D Liver Tumor Segmentation API (Minimal)", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/register")
def register(req: UserAuthRequest):
    username = req.username.strip()
    password = req.password
    if not username:
        raise HTTPException(status_code=400, detail="username cannot be empty")
    if not password:
        raise HTTPException(status_code=400, detail="password cannot be empty")

    with db.get_session() as session:
        if crud.get_user_by_username(session, username) is not None:
            raise HTTPException(status_code=409, detail="username already exists")
        user = crud.create_user(session, username, _hash_password(password))
    return user


@app.post("/login")
def login(req: UserAuthRequest):
    username = req.username.strip()
    password = req.password
    with db.get_session() as session:
        user = crud.get_user_entity_by_username(session, username)
    if user is None or not _verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"id": user.id, "username": user.username}


@app.post("/predict")
def predict(file: UploadFile = File(...)):
    upload_path, original_filename = _save_upload_file(file)

    start = time.time()
    try:
        output_name = f"result-{Path(original_filename).name}"
        result_path = run_predict(upload_path, output_name=output_name)
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "filename": original_filename,
            "result_path": result_path,
            "elapsed_ms": elapsed_ms,
        }
    finally:
        _safe_remove(upload_path)


@app.post("/predict_by_path")
def predict_by_path(req: PredictRequest):
    start = time.time()
    result_path = run_predict(req.ct_path)
    elapsed_ms = int((time.time() - start) * 1000)
    return {"result_path": result_path, "elapsed_ms": elapsed_ms}


@app.post("/jobs")
def create_job(file: UploadFile = File(...)):
    upload_path, original_filename = _save_upload_file(file)
    job_id = uuid.uuid4().hex
    with db.get_session() as session:
        crud.create_job(session, job_id, upload_path, original_filename)
    try:
        executor.submit(_run_job, job_id, upload_path, original_filename)
    except Exception:
        _safe_remove(upload_path)
        raise
    return {"job_id": job_id, "status": "pending"}


@app.post("/me/jobs")
def create_my_job(file: UploadFile = File(...), current_user: dict = Depends(_require_user)):
    upload_path, original_filename = _save_upload_file(file)
    job_id = uuid.uuid4().hex
    with db.get_session() as session:
        crud.create_job(session, job_id, upload_path, original_filename, user_id=current_user["id"])
    try:
        executor.submit(_run_job, job_id, upload_path, original_filename)
    except Exception:
        _safe_remove(upload_path)
        raise
    return {"job_id": job_id, "status": "pending"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with db.get_session() as session:
        job = crud.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/me/jobs")
def list_my_jobs(limit: int = 20, current_user: dict = Depends(_require_user)):
    limit = max(1, min(limit, 100))
    with db.get_session() as session:
        items = crud.list_jobs(session, user_id=current_user["id"], limit=limit)
    return {"items": items, "count": len(items)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_min:app", host="0.0.0.0", port=8000)
