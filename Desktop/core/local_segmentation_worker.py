import os
import time

import numpy as np
import SimpleITK as sitk
import torch
from PyQt5 import QtCore
from torch.utils.data import DataLoader

from Desktop.core.inference import Test_DataSet


class LocalSegmentationWorker(QtCore.QObject):
    progress_changed = QtCore.pyqtSignal(int)
    succeeded = QtCore.pyqtSignal(str, str, int)
    failed = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, model, device, ct_path, args):
        super().__init__()
        self.model = model
        self.device = device
        self.ct_path = ct_path
        self.args = args

    def _predict(self, ct_dataset):
        dataloader = DataLoader(dataset=ct_dataset, batch_size=1, num_workers=0, shuffle=False)
        total_steps = max(1, len(dataloader))
        self.model.eval()

        with torch.no_grad():
            for index, data in enumerate(dataloader, start=1):
                data = data.to(self.device)
                output = self.model(data)
                output = torch.nn.functional.interpolate(
                    output,
                    scale_factor=(
                        1 / self.args.z_down_scale,
                        1 / self.args.xy_down_scale,
                        1 / self.args.xy_down_scale,
                    ),
                    mode="trilinear",
                    align_corners=False,
                )
                ct_dataset.update_result(output.detach().cpu())
                self.progress_changed.emit(int(index / total_steps * 100))

        pred = ct_dataset.recompone_result()
        pred = torch.argmax(pred, dim=1)
        pred_np = np.squeeze(pred.numpy(), axis=0).astype(np.uint8)

        pred_ct = sitk.GetImageFromArray(pred_np)
        pred_ct.SetDirection(ct_dataset.ct.GetDirection())
        pred_ct.SetOrigin(ct_dataset.ct.GetOrigin())
        pred_ct.SetSpacing(ct_dataset.ct.GetSpacing())
        return pred_ct

    @QtCore.pyqtSlot()
    def run(self):
        start_time = time.time()
        try:
            result_save_path = os.path.join(self.args.log_save, "result")
            os.makedirs(result_save_path, exist_ok=True)

            ct_dataset = Test_DataSet(self.ct_path, None, args=self.args)
            pred_ct = self._predict(ct_dataset)

            ct_name = os.path.basename(self.ct_path).split("-")[-1]
            segmentation_path = os.path.join(result_save_path, f"result-{ct_name}")
            sitk.WriteImage(pred_ct, segmentation_path)

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.succeeded.emit(segmentation_path, ct_name, elapsed_ms)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()
