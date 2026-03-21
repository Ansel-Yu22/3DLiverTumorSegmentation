import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
import SimpleITK as sitk
import torch
from fastapi import UploadFile
from scipy import ndimage
from torch.utils.data import DataLoader, Dataset

from model.model import UNet
from app import state
from app.persistence import crud, db


class InferenceDataset(Dataset):
    def __init__(self, ct_path: str):
        self.n_label = state.N_LABEL
        self.cut_size = state.TC_SIZE
        self.cut_stride = state.TC_STRIDE

        self.ct = sitk.ReadImage(ct_path, sitk.sitkInt16)
        self.ct_np = sitk.GetArrayFromImage(self.ct)
        self.ori_shape = self.ct_np.shape

        self.ct_np = ndimage.zoom(
            self.ct_np,
            (state.Z_DOWN_SCALE, state.XY_DOWN_SCALE, state.XY_DOWN_SCALE),
            order=3,
        )

        self.ct_np[self.ct_np > state.UPPER] = state.UPPER
        self.ct_np[self.ct_np < state.LOWER] = state.LOWER
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


def safe_remove(path: Optional[str]) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        # Best-effort cleanup; do not fail request/job flow.
        pass


def build_result_filename(source_name: str) -> str:
    base_name = Path(str(source_name)).name
    suffix = base_name.split("-")[-1] if "-" in base_name else base_name
    if not suffix:
        suffix = base_name
    return f"result-{suffix}"


def save_upload_file(file: UploadFile) -> tuple[str, str]:
    suffixes = "".join(Path(file.filename).suffixes)
    suffix = suffixes if suffixes else ".nii"
    upload_name = f"{uuid.uuid4().hex}{suffix}"
    upload_path = os.path.join(state.UPLOAD_DIR, upload_name)
    try:
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        try:
            file.file.close()
        except Exception:
            pass
    return upload_path, file.filename


def run_predict(ct_path: str, output_name: Optional[str] = None) -> str:
    dataset = InferenceDataset(ct_path)
    dataloader = DataLoader(dataset=dataset, batch_size=1, num_workers=0, shuffle=False)

    state.model.eval()
    with torch.no_grad():
        for data in dataloader:
            data = data.to(state.device)
            output = state.model(data)
            output = torch.nn.functional.interpolate(
                output,
                scale_factor=(1 / state.Z_DOWN_SCALE, 1 / state.XY_DOWN_SCALE, 1 / state.XY_DOWN_SCALE),
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

    out_name = output_name if output_name else build_result_filename(ct_path)
    out_path = os.path.join(state.RESULT_DIR, out_name)
    sitk.WriteImage(pred_img, out_path)
    return out_path


def run_job(job_id: str, upload_path: str, original_filename: str) -> None:
    with db.get_session() as session:
        crud.update_job(session, job_id, "running")

    start = time.time()
    try:
        output_name = build_result_filename(original_filename)
        result_path = run_predict(upload_path, output_name=output_name)
        elapsed_ms = int((time.time() - start) * 1000)
        with db.get_session() as session:
            crud.update_job(session, job_id, "succeeded", result_path=result_path, elapsed_ms=elapsed_ms, error=None)
    except Exception as exc:
        elapsed_ms = int((time.time() - start) * 1000)
        with db.get_session() as session:
            crud.update_job(session, job_id, "failed", result_path=None, elapsed_ms=elapsed_ms, error=str(exc))
    finally:
        safe_remove(upload_path)


def load_state_dict(model_path: str):
    try:
        checkpoint = torch.load(model_path, map_location=state.device, weights_only=True)
    except TypeError:
        checkpoint = torch.load(model_path, map_location=state.device)

    if isinstance(checkpoint, dict) and "net" in checkpoint:
        state_dict = checkpoint["net"]
    elif isinstance(checkpoint, dict):
        state_dict = checkpoint
    else:
        raise ValueError("Unsupported checkpoint format: expected dict or dict with key 'net'.")

    if any(k.startswith("module.") for k in state_dict.keys()):
        state_dict = {k.replace("module.", "", 1): v for k, v in state_dict.items()}
    return state_dict


def startup_init() -> None:
    os.makedirs(state.RESULT_DIR, exist_ok=True)
    os.makedirs(state.UPLOAD_DIR, exist_ok=True)
    db.init_db(db_url=state.DB_URL or None)
    net = UNet(in_channel=1, out_channel=state.N_LABEL, drop_rate=state.DROP_RATE, training=False)
    net = net.to(state.device)
    loaded_state_dict = load_state_dict(state.MODEL_PATH)
    net.load_state_dict(loaded_state_dict)
    state.model = net



