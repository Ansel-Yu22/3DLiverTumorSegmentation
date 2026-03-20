import os
import time

import config
import nibabel as nib
import numpy as np
import SimpleITK as sitk
import torch
from PyQt5.QtWidgets import QApplication, QMessageBox
from torch.utils.data import DataLoader

from Desktop.inference import MetricsCalculator, Test_DataSet


class LocalSegmentationControllerMixin:
    def segmentation(self):
        if not self.ui.lineEdit_CT_path.text():
            QMessageBox.information(self, "提示", "请先选择CT", QMessageBox.Yes)
            return
        start_time = time.time()
        args = config.args
        self.result_save_path = f"{args.log_save}/result"
        if not os.path.exists(self.result_save_path):
            os.mkdir(self.result_save_path)
        ct_path = self.ui.lineEdit_CT_path.text()
        datasets = self.Test_Datasets(ct_path, None, args)
        for ct_dataset, self.ct_name in datasets:
            _, pred_ct = self.predict(self.model, ct_dataset, args)
            self.segmentation_path = os.path.join(self.result_save_path, f"result-{self.ct_name}")
            sitk.WriteImage(pred_ct, self.segmentation_path)
        nii_img = nib.load(self.segmentation_path)
        self.segmentation_data = nii_img.get_fdata()
        self.display_slice()
        self._refresh_action_buttons()
        elapsed_ms = int((time.time() - start_time) * 1000)
        local_job_id = f"local-{int(start_time)}"
        self._show_segmentation_success("local", local_job_id, elapsed_ms)

    def predict(self, model, ct_dataset, args):
        dataloader = DataLoader(dataset=ct_dataset, batch_size=1, num_workers=0, shuffle=False)
        model.eval()
        total_steps = len(dataloader)
        with torch.no_grad():
            for i, data in enumerate(dataloader):
                data = data.to(self.device)
                output = model(data)
                output = torch.nn.functional.interpolate(
                    output,
                    scale_factor=(1 / args.z_down_scale, 1 / args.xy_down_scale, 1 / args.xy_down_scale),
                    mode="trilinear",
                    align_corners=False,
                )
                ct_dataset.update_result(output.detach().cpu())
                self.ui.progressBar.setValue(int((i + 1) / total_steps * 100))
                QApplication.processEvents()
        pred = ct_dataset.recompone_result()
        pred = torch.argmax(pred, dim=1)
        pred_ct = sitk.GetImageFromArray(np.squeeze(pred.numpy(), axis=0).astype(np.uint8))
        return None, pred_ct

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

    def to_one_hot_3d(self, tensor, n_label):
        n, s, h, w = tensor.size()
        one_hot = torch.zeros(n, n_label, s, h, w)
        one_hot = one_hot.scatter_(1, tensor.view(n, 1, s, h, w), 1)
        return one_hot

    def Test_Datasets(self, ct_path, label_path, args):
        ct_list = [ct_path]
        label_list = [label_path] if label_path else [None]
        for ct_file, label_file in zip(ct_list, label_list):
            yield Test_DataSet(ct_file, label_file, args=args), ct_file.split("-")[-1]
