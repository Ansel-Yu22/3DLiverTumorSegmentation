import os
import time

import config
import nibabel as nib
import torch
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox

from Desktop.core.inference import MetricsCalculator
from Desktop.core.local_segmentation_worker import LocalSegmentationWorker


class LocalSegmentationControllerMixin:
    def segmentation(self):
        if self.local_seg_in_progress:
            QMessageBox.information(self, "提示", "本地分割任务正在运行，请稍候。", QMessageBox.Yes)
            return
        if self.api_poll_context is not None:
            QMessageBox.information(self, "提示", "已有 API 任务在运行，请稍候。", QMessageBox.Yes)
            return

        ct_path = self.ui.lineEdit_CT_path.text().strip()
        if not ct_path:
            QMessageBox.information(self, "提示", "请先选择CT", QMessageBox.Yes)
            return
        if not os.path.exists(ct_path):
            QMessageBox.critical(self, "错误", f"CT 文件不存在:\n{ct_path}", QMessageBox.Yes)
            return

        self.ui.lineEdit_Dice.setText("")
        self.ui.lineEdit_iou.setText("")
        self.ui.progressBar.setValue(0)

        self._start_local_segmentation_worker(ct_path)

    def _start_local_segmentation_worker(self, ct_path):
        args = config.args
        self._local_seg_thread = QtCore.QThread(self)
        self._local_seg_worker = LocalSegmentationWorker(
            model=self.model,
            device=self.device,
            ct_path=ct_path,
            args=args,
        )
        self._local_seg_worker.moveToThread(self._local_seg_thread)

        self._local_seg_thread.started.connect(self._local_seg_worker.run)
        self._local_seg_worker.progress_changed.connect(self.ui.progressBar.setValue)
        self._local_seg_worker.succeeded.connect(self._on_local_segmentation_succeeded)
        self._local_seg_worker.failed.connect(self._on_local_segmentation_failed)
        self._local_seg_worker.finished.connect(self._local_seg_thread.quit)
        self._local_seg_worker.finished.connect(self._local_seg_worker.deleteLater)
        self._local_seg_thread.finished.connect(self._local_seg_thread.deleteLater)
        self._local_seg_thread.finished.connect(self._on_local_segmentation_finished)

        self.local_seg_in_progress = True
        self._refresh_action_buttons()
        self._local_seg_thread.start()

    def _on_local_segmentation_succeeded(self, segmentation_path, ct_name, elapsed_ms):
        self.segmentation_path = segmentation_path
        self.ct_name = ct_name
        self.segmentation_data = nib.load(self.segmentation_path).get_fdata()
        self.ui.progressBar.setValue(100)
        self.display_slice()
        self._refresh_action_buttons()

        local_job_id = f"local-{int(time.time())}"
        self._show_segmentation_success("local", local_job_id, elapsed_ms)

    def _on_local_segmentation_failed(self, error_message):
        self.ui.progressBar.setValue(0)
        QMessageBox.critical(self, "错误", f"本地分割失败:\n{error_message}", QMessageBox.Yes)

    def _on_local_segmentation_finished(self):
        self.local_seg_in_progress = False
        self._local_seg_worker = None
        self._local_seg_thread = None
        self._refresh_action_buttons()

    def calculate_metrics(self):
        if self.segmentation_data is None or self.label_data is None:
            return None, None
        if self.segmentation_data.shape != self.label_data.shape:
            return None, None

        args = config.args
        pred = torch.from_numpy(self.segmentation_data).unsqueeze(0).long()
        target = torch.from_numpy(self.label_data).unsqueeze(0).long()
        pred_one_hot = self.to_one_hot_3d(pred, args.n_label)
        target_one_hot = self.to_one_hot_3d(target, args.n_label)

        metrics_calc = MetricsCalculator(args.n_label)
        metrics_calc.update(pred_one_hot, target_one_hot)
        dice_avg, iou_avg = metrics_calc.get_averages()
        if args.n_label == 3:
            return dice_avg[2], iou_avg[2]
        return dice_avg[0], iou_avg[0]

    @staticmethod
    def to_one_hot_3d(tensor, n_label):
        n, s, h, w = tensor.size()
        one_hot = torch.zeros(n, n_label, s, h, w, device=tensor.device, dtype=torch.float32)
        return one_hot.scatter_(1, tensor.view(n, 1, s, h, w), 1)
