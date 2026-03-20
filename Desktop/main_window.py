import base64
import os
import shutil
from datetime import datetime

import nibabel as nib
import numpy as np
import torch
from Model.model import UNet
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from Desktop.api_client import ApiClient
from Desktop.api_task_controller import ApiTaskControllerMixin
from Desktop.local_segmentation_controller import LocalSegmentationControllerMixin
from Desktop.ui_layout import Ui_MainWindow
from Desktop.views import AccountDialog


__version__ = "2.0.0"


class MainWindow(QMainWindow, ApiTaskControllerMixin, LocalSegmentationControllerMixin):
    def __init__(self, api_base_url=None, auth_username=None, auth_password=None, auth_user_id=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.action_about.triggered.connect(self.show_about)
        self.ui.action_account.triggered.connect(self.open_account_dialog)
        self.init_slot()

        self._load_model()

        self.current_slice_index = 0
        self.ct_data = None
        self.label_data = None
        self.segmentation_data = None
        self.segmentation_path = None

        default_api = os.environ.get("SEG_API_BASE_URL", "http://127.0.0.1:8000")
        self.api_base_url = (api_base_url or default_api).rstrip("/")
        self.api_client = ApiClient(self.api_base_url)
        self.api_poll_interval_sec = 2
        self.api_timeout_sec = 600
        self.api_poll_timer = QtCore.QTimer(self)
        self.api_poll_timer.timeout.connect(self._poll_api_job_once)
        self.api_poll_context = None
        self.local_seg_in_progress = False
        self._local_seg_thread = None
        self._local_seg_worker = None

        self.auth_username = auth_username
        self.auth_password = auth_password
        self.auth_user_id = auth_user_id
        self.account_dialog = None

        self._init_status_bar()
        self._update_account_status()
        self._refresh_action_buttons()

    def _load_model(self):
        import config

        args = config.args
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = UNet(in_channel=1, out_channel=args.n_label, drop_rate=args.drop_rate, training=False)
        self.model = torch.nn.DataParallel(self.model)
        self.model = self.model.to(self.device)
        checkpoint = torch.load(f"{args.model_save}/best_model.pth", map_location=self.device)
        self.model.load_state_dict(checkpoint["net"])

    def show_about(self):
        html = (
            "<h3>肝脏肿瘤CT分割系统</h3>"
            f"<p><b>版本：</b>{__version__}</p>"
            "<p><b>作者：</b>于波</p>"
            "<p><b>机构：</b>桂林电子科技大学</p>"
            "<p><b>编译日期：</b>2026-03-20</p>"
            "<hr>"
            "<p>本系统基于LDR-UNet模型构建，实现肝脏及肿瘤CT影像的自动分割、"
            "分割结果保存与评估等功能。</p>"
        )
        QMessageBox.about(self, "关于", html)

    def init_slot(self):
        self.ui.pushButton_CT.clicked.connect(self.load_CT)
        self.ui.pushButton_label.clicked.connect(self.load_label)
        self.ui.pushButton_segmentation.clicked.connect(self.segmentation)
        self.ui.pushButton_segmentation_api.clicked.connect(self.segmentation_api)
        self.ui.pushButton_save.clicked.connect(self.save)
        self.ui.pushButton_info.clicked.connect(self.info)
        self.ui.pushButton_next.clicked.connect(self.next_slice)
        self.ui.pushButton_previous.clicked.connect(self.previous_slice)

    def _refresh_action_buttons(self):
        has_ct = bool(self.ui.lineEdit_CT_path.text().strip())
        has_result = self.segmentation_data is not None and bool(self.segmentation_path)
        is_polling = self.api_poll_context is not None and self.api_poll_timer.isActive()
        is_local_running = bool(getattr(self, "local_seg_in_progress", False))
        can_start_seg = has_ct and not is_polling and not is_local_running
        self.ui.pushButton_segmentation.setEnabled(can_start_seg)
        self.ui.pushButton_segmentation_api.setEnabled(can_start_seg)
        self.ui.pushButton_save.setEnabled(has_result)
        self.ui.pushButton_info.setEnabled(has_result)

    def _init_status_bar(self):
        status_bar = self.statusBar()
        status_bar.setVisible(True)
        if not hasattr(self, "status_left_label"):
            self.status_left_label = QtWidgets.QLabel("")
            self.status_left_label.setStyleSheet("padding-left: 6px; color: #334155;")
            status_bar.addWidget(self.status_left_label, 1)
        if not hasattr(self, "status_time_label"):
            self.status_time_label = QtWidgets.QLabel("")
            self.status_time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.status_time_label.setStyleSheet("padding-right: 6px; color: #64748b;")
            status_bar.addPermanentWidget(self.status_time_label)
        if not hasattr(self, "status_clock_timer"):
            self.status_clock_timer = QtCore.QTimer(self)
            self.status_clock_timer.timeout.connect(self._update_status_time)
            self.status_clock_timer.start(1000)
        self._update_status_time()

    def _update_status_time(self):
        if hasattr(self, "status_time_label"):
            self.status_time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def _format_elapsed_seconds(elapsed_ms):
        try:
            if elapsed_ms is None:
                return "-"
            return f"{float(elapsed_ms) / 1000.0:.2f}"
        except (TypeError, ValueError):
            return "-"

    def _show_segmentation_success(self, mode_text, job_id, elapsed_ms):
        elapsed_s = self._format_elapsed_seconds(elapsed_ms)
        QMessageBox.information(
            self,
            "提示",
            f"分割成功\n模式: {mode_text}\n任务ID: {job_id}\n耗时: {elapsed_s} s",
            QMessageBox.Yes,
        )

    def _update_account_status(self):
        status_bar = self.statusBar()
        status_bar.setVisible(True)
        if not hasattr(self, "status_left_label"):
            self._init_status_bar()
        if self.is_user_logged_in():
            status_text = f"API: {self.api_base_url} | 已登录: {self.auth_username}"
        else:
            status_text = f"API: {self.api_base_url} | 未登录"
        self.status_left_label.setText(status_text)
        status_bar.clearMessage()

    def set_api_base_url(self, base_url):
        value = (base_url or "").strip()
        if not value:
            value = "http://127.0.0.1:8000"
        self.api_base_url = value.rstrip("/")
        self.api_client.set_base_url(self.api_base_url)
        self._update_account_status()

    def is_user_logged_in(self):
        return bool(self.auth_username and self.auth_password)

    def _auth_header(self):
        if not self.is_user_logged_in():
            return None
        token = base64.b64encode(f"{self.auth_username}:{self.auth_password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    def _request_json(self, method, path, payload=None, auth_header=None, timeout=30):
        return self.api_client.request_json(method, path, payload=payload, auth_header=auth_header, timeout=timeout)

    def api_logout_user(self):
        self.auth_username = None
        self.auth_password = None
        self.auth_user_id = None
        self._update_account_status()

    def api_list_my_jobs(self, limit=20):
        auth_header = self._auth_header()
        if not auth_header:
            raise RuntimeError("未登录")
        return self._request_json("GET", f"/me/jobs?limit={limit}", auth_header=auth_header, timeout=30)

    def open_account_dialog(self):
        if self.account_dialog is None:
            self.account_dialog = AccountDialog(self)
        self.account_dialog._update_view()
        if self.is_user_logged_in():
            self.account_dialog._on_refresh_jobs()
        self.account_dialog.exec_()

    def _load_volume_data(self, path, path_line_edit, size_line_edit):
        path_line_edit.setText(path)
        file_size = os.path.getsize(path)
        size_line_edit.setText(f"{file_size / (1024 * 1024):.2f} MB")
        return nib.load(path).get_fdata()

    def load_CT(self):
        path, _ = QFileDialog.getOpenFileName(None, "选择CT影像", "./Doc/ct/ct", "CT File (*.nii *.nii.gz)")
        if not path:
            return
        self.ui.lineEdit_Dice.setText("")
        self.ui.lineEdit_iou.setText("")
        self.ui.progressBar.setValue(0)
        self.ct_data = self._load_volume_data(path, self.ui.lineEdit_CT_path, self.ui.lineEdit_Ct_size)
        self.current_slice_index = self.ct_data.shape[2] // 2
        self.segmentation_data = None
        self.segmentation_path = None
        self.display_slice()
        self._refresh_action_buttons()

    def load_label(self):
        path, _ = QFileDialog.getOpenFileName(None, "选择标注影像", "./Doc/ct/label", "Label File (*.nii *.nii.gz)")
        if not path:
            return
        self.label_data = self._load_volume_data(path, self.ui.lineEdit_label_path, self.ui.lineEdit_label_size)
        if self.ct_data is not None:
            self.display_slice()

    def save(self):
        if self.segmentation_path is None:
            QMessageBox.information(self, "提示", "请先进行分割后再保存", QMessageBox.Yes)
            return
        settings = QSettings("MyApp", "SaveSettings")
        last_path = settings.value("last_save_path", "")
        src_file = self.segmentation_path
        if not os.path.exists(src_file):
            QMessageBox.critical(self, "错误", "源文件不存在，无法保存", QMessageBox.Yes)
            return
        default_name = f"result-{self.ct_name}"
        file_filter = "NIFTI 文件 (*.nii);;压缩 NIFTI (*.nii.gz)"
        while True:
            folder_path, selected_filter = QFileDialog.getSaveFileName(
                self, "保存分割结果", os.path.join(last_path, default_name), file_filter
            )
            if not folder_path:
                return
            suffix = ".nii" if selected_filter.startswith("NIFTI 文件") else ".nii.gz"
            base = folder_path
            while True:
                lower = base.lower()
                if lower.endswith(".nii.gz"):
                    base = base[:-7]
                elif lower.endswith(".nii"):
                    base = base[:-4]
                elif lower.endswith(".gz"):
                    base = base[:-3]
                else:
                    break
            folder_path = base + suffix
            break
        try:
            if folder_path.lower().endswith(".nii.gz"):
                import gzip

                with open(src_file, "rb") as f_in, gzip.open(folder_path, "wb") as f_out:
                    while True:
                        chunk = f_in.read(1024 * 1024)
                        if not chunk:
                            break
                        f_out.write(chunk)
            else:
                shutil.copy(src_file, folder_path)
            settings.setValue("last_save_path", os.path.dirname(folder_path))
            QMessageBox.information(self, "提示", "保存成功", QMessageBox.Yes)
        except Exception as exc:
            QMessageBox.critical(self, "错误", f"保存失败: {exc}", QMessageBox.Yes)

    def info(self):
        if self.segmentation_data is None:
            QMessageBox.information(self, "提示", "请先进行分割", QMessageBox.Yes)
            return
        if self.label_data is None:
            QMessageBox.information(self, "提示", "请先加载标注", QMessageBox.Yes)
            return
        dice, iou = self.calculate_metrics()
        if dice is not None and iou is not None:
            self.ui.lineEdit_Dice.setText(f"{dice:.4f}")
            self.ui.lineEdit_iou.setText(f"{iou:.4f}")
        else:
            QMessageBox.warning(self, "警告", "分割结果与标注数据形状不匹配，无法计算指标", QMessageBox.Yes)

    @staticmethod
    def _normalize_slice_to_uint8(slice_data):
        min_value = float(slice_data.min())
        max_value = float(slice_data.max())
        if max_value <= min_value:
            return np.zeros_like(slice_data, dtype=np.uint8)
        normalized = (slice_data - min_value) / (max_value - min_value)
        return (normalized * 255).astype(np.uint8)

    def _render_slice_to_label(self, volume_data, target_label):
        if volume_data is None:
            return
        slice_data = volume_data[:, :, self.current_slice_index]
        slice_data = self._normalize_slice_to_uint8(slice_data)
        height, width = slice_data.shape
        bytes_per_line = width
        qimage = QImage(slice_data.tobytes(), width, height, bytes_per_line, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        label_size = target_label.size()
        scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        target_label.setPixmap(scaled_pixmap)

    def display_slice(self):
        self._render_slice_to_label(self.ct_data, self.ui.label_ct)
        self._render_slice_to_label(self.label_data, self.ui.label_label)
        self._render_slice_to_label(self.segmentation_data, self.ui.label_segmentation)
        if self.ct_data is not None:
            total_slices = self.ct_data.shape[2]
            self.ui.label_slice_info.setText(f"切片: {self.current_slice_index + 1} / {total_slices}")

    def next_slice(self):
        if self.ct_data is not None and self.current_slice_index < self.ct_data.shape[2] - 1:
            self.current_slice_index += 1
            self.display_slice()

    def previous_slice(self):
        if self.ct_data is not None and self.current_slice_index > 0:
            self.current_slice_index -= 1
            self.display_slice()
