import base64
import os
import time
import urllib.error
from datetime import datetime

import config
import nibabel as nib
import numpy as np
import SimpleITK as sitk
import shutil
import torch
from Model.Model import UNet
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QColor, QImage, QPalette, QPixmap
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from torch.utils.data import DataLoader

from Desktop.api_client import ApiClient
from Desktop.inference import MetricsCalculator, Test_DataSet
from Desktop.views import AccountDialog
from path_utils import resolve_result_path


__version__ = '2.0.0'


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1038, 666)
        MainWindow.setMinimumSize(980, 640)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f5f5f5"))
        MainWindow.setPalette(palette)
        menubar = MainWindow.menuBar()
        account_menu = menubar.addMenu("账号(&U)")
        account_action = QtWidgets.QAction("账号中心(&C)", MainWindow)
        account_menu.addAction(account_action)
        self.action_account = account_action
        help_menu = menubar.addMenu('帮助(&H)')
        about_action = QtWidgets.QAction('关于(&A)', MainWindow)
        help_menu.addAction(about_action)
        self.action_about = about_action
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.kai_font_12 = QtGui.QFont("楷体", 12)
        self.kai_font_14 = QtGui.QFont("楷体", 14)
        self.kai_font_16 = QtGui.QFont("楷体", 16)
        self.times_font_14 = QtGui.QFont("Times New Roman", 14)
        self.button_style = """
            QPushButton {
                border: 1px solid #c8d3df;
                border-radius: 12px;
                background-color: #f1f5f9;
                color: #1f2937;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                border-color: #94a3b8;
            }
            QPushButton:pressed { background-color: #dbe4ef; }
        """
        self.action_primary_style = """
            QPushButton {
                border: none;
                border-radius: 12px;
                background-color: #2f7dd1;
                color: white;
                font-weight: 600;
                padding: 6px 10px;
            }
            QPushButton:hover { background-color: #256db8; }
            QPushButton:pressed { background-color: #1f5a98; }
        """
        self.action_secondary_style = """
            QPushButton {
                border: 1px solid #9fb6cc;
                border-radius: 12px;
                background-color: #e8f0f8;
                color: #133a5f;
                font-weight: 600;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background-color: #d8e6f3;
                border-color: #7d9fbd;
            }
            QPushButton:pressed { background-color: #c8daeb; }
        """
        self.lineedit_style = "border: 1px solid #c8d3df; background-color: #fff; border-radius: 10px; padding: 6px 10px; color:#334155;"
        self.label_style = "border: 1px solid #c8d3df; background-color: #fff; border-radius: 10px;"
        self.pushButton_CT = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_CT.setGeometry(QtCore.QRect(50, 50, 150, 50))
        self.pushButton_CT.setFont(self.kai_font_14)
        self.pushButton_CT.setText("加载CT")
        self.pushButton_CT.setStyleSheet(self.button_style)
        self.pushButton_CT.setToolTip("选择CT影像文件")
        self.lineEdit_CT_path = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_CT_path.setGeometry(QtCore.QRect(229, 50, 400, 50))
        self.lineEdit_CT_path.setFont(self.kai_font_14)
        self.lineEdit_CT_path.setAlignment(Qt.AlignCenter)
        self.lineEdit_CT_path.setReadOnly(True)
        self.lineEdit_CT_path.setStyleSheet(self.lineedit_style)
        self.lineEdit_CT_path.setPlaceholderText("CT文件路径")
        self.lineEdit_CT_path.textChanged.connect(
            lambda text: self.lineEdit_CT_path.setFont(self.times_font_14 if text else self.kai_font_14)
        )
        self.lineEdit_CT_path.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_Ct_size = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_Ct_size.setGeometry(QtCore.QRect(658, 50, 150, 50))
        self.lineEdit_Ct_size.setFont(self.kai_font_14)
        self.lineEdit_Ct_size.setAlignment(Qt.AlignCenter)
        self.lineEdit_Ct_size.setReadOnly(True)
        self.lineEdit_Ct_size.setStyleSheet(self.lineedit_style)
        self.lineEdit_Ct_size.setPlaceholderText("文件大小")
        self.lineEdit_Ct_size.textChanged.connect(
            lambda text: self.lineEdit_Ct_size.setFont(self.times_font_14 if text else self.kai_font_14)
        )
        self.lineEdit_Ct_size.setFocusPolicy(Qt.NoFocus)
        self.pushButton_label = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_label.setGeometry(QtCore.QRect(50, 120, 150, 50))
        self.pushButton_label.setFont(self.kai_font_14)
        self.pushButton_label.setText("加载标注")
        self.pushButton_label.setStyleSheet(self.button_style)
        self.pushButton_label.setToolTip("选择标注影像文件")
        self.lineEdit_label_path = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_label_path.setGeometry(QtCore.QRect(229, 120, 400, 50))
        self.lineEdit_label_path.setFont(self.kai_font_14)
        self.lineEdit_label_path.setAlignment(Qt.AlignCenter)
        self.lineEdit_label_path.setReadOnly(True)
        self.lineEdit_label_path.setStyleSheet(self.lineedit_style)
        self.lineEdit_label_path.setPlaceholderText("标注文件路径")
        self.lineEdit_label_path.textChanged.connect(
            lambda text: self.lineEdit_label_path.setFont(self.times_font_14 if text else self.kai_font_14)
        )
        self.lineEdit_label_path.setFocusPolicy(Qt.NoFocus)
        self.lineEdit_label_size = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_label_size.setGeometry(QtCore.QRect(658, 120, 150, 50))
        self.lineEdit_label_size.setFont(self.kai_font_14)
        self.lineEdit_label_size.setAlignment(Qt.AlignCenter)
        self.lineEdit_label_size.setReadOnly(True)
        self.lineEdit_label_size.setStyleSheet(self.lineedit_style)
        self.lineEdit_label_size.setPlaceholderText("文件大小")
        self.lineEdit_label_size.textChanged.connect(
            lambda text: self.lineEdit_label_size.setFont(self.times_font_14 if text else self.kai_font_14)
        )
        self.lineEdit_label_size.setFocusPolicy(Qt.NoFocus)
        self.label_ct = QtWidgets.QLabel(self.centralwidget)
        self.label_ct.setGeometry(QtCore.QRect(30, 220, 256, 256))
        self.label_ct.setFont(self.kai_font_16)
        self.label_ct.setText("CT切片")
        self.label_ct.setAlignment(Qt.AlignCenter)
        self.label_ct.setStyleSheet(self.label_style)
        self.label_label = QtWidgets.QLabel(self.centralwidget)
        self.label_label.setGeometry(QtCore.QRect(301, 220, 256, 256))
        self.label_label.setFont(self.kai_font_16)
        self.label_label.setText("标注切片")
        self.label_label.setAlignment(Qt.AlignCenter)
        self.label_label.setStyleSheet(self.label_style)
        self.label_segmentation = QtWidgets.QLabel(self.centralwidget)
        self.label_segmentation.setGeometry(QtCore.QRect(572, 220, 256, 256))
        self.label_segmentation.setFont(self.kai_font_16)
        self.label_segmentation.setText("分割切片")
        self.label_segmentation.setAlignment(Qt.AlignCenter)
        self.label_segmentation.setStyleSheet(self.label_style)
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(30, 496, 798, 20))
        self.progressBar.setFont(self.kai_font_14)
        self.progressBar.setValue(0)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #c8d3df;
                border-radius: 10px;
                background: #eef2f7;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 10px;
            }
        """)
        self.pushButton_previous = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_previous.setGeometry(QtCore.QRect(200, 536, 100, 40))
        self.pushButton_previous.setFont(self.kai_font_12)
        self.pushButton_previous.setText("上一张")
        self.pushButton_previous.setStyleSheet(self.button_style)
        self.pushButton_previous.setToolTip("显示上一张切片")
        self.label_slice_info = QtWidgets.QLabel(self.centralwidget)
        self.label_slice_info.setGeometry(QtCore.QRect(329, 536, 200, 40))
        self.label_slice_info.setFont(self.kai_font_12)
        self.label_slice_info.setAlignment(Qt.AlignCenter)
        self.label_slice_info.setText("切片:  0 / 0")
        self.label_slice_info.setStyleSheet(self.lineedit_style)
        self.pushButton_next = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_next.setGeometry(QtCore.QRect(558, 536, 100, 40))
        self.pushButton_next.setFont(self.kai_font_12)
        self.pushButton_next.setText("下一张")
        self.pushButton_next.setStyleSheet(self.button_style)
        self.pushButton_next.setToolTip("显示下一张切片")
        self.pushButton_segmentation = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_segmentation.setGeometry(QtCore.QRect(858, 50, 150, 46))
        self.pushButton_segmentation.setFont(self.kai_font_14)
        self.pushButton_segmentation_api = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_segmentation_api.setGeometry(QtCore.QRect(858, 106, 150, 46))
        self.pushButton_segmentation_api.setFont(self.kai_font_14)
        self.pushButton_segmentation_api.setText("API分割")
        self.pushButton_segmentation_api.setStyleSheet(self.action_primary_style)
        self.pushButton_segmentation_api.setToolTip("通过后端 API 执行异步分割")
        self.pushButton_segmentation.setText("分割")
        self.pushButton_segmentation.setStyleSheet(self.action_primary_style)
        self.pushButton_segmentation.setToolTip("执行肝脏肿瘤CT分割")
        self.pushButton_save = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_save.setGeometry(QtCore.QRect(858, 162, 150, 46))
        self.pushButton_save.setFont(self.kai_font_14)
        self.pushButton_save.setText("保存")
        self.pushButton_save.setStyleSheet(self.action_secondary_style)
        self.pushButton_save.setToolTip("保存分割结果")
        self.pushButton_info = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_info.setGeometry(QtCore.QRect(858, 218, 150, 46))
        self.pushButton_info.setFont(self.kai_font_14)
        self.pushButton_info.setText("评价")
        self.pushButton_info.setStyleSheet(self.action_secondary_style)
        self.pushButton_info.setToolTip("显示分割指标")
        self.label_metrics_title = QtWidgets.QLabel(self.centralwidget)
        self.label_metrics_title.setGeometry(QtCore.QRect(858, 286, 150, 28))
        self.label_metrics_title.setFont(self.kai_font_14)
        self.label_metrics_title.setText("分割指标")
        self.label_metrics_title.setAlignment(Qt.AlignCenter)
        self.label_metrics_title.setStyleSheet("background: transparent; color: #334155;")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(858, 318, 150, 258))
        self.groupBox.setFont(self.kai_font_14)
        self.groupBox.setTitle("")
        self.groupBox.setAlignment(Qt.AlignCenter)
        self.groupBox.setStyleSheet(""" QGroupBox { background:#fff; border:1px solid #c8d3df; border-radius: 10px; margin-top:0px; } """)
        self.label_dice = QtWidgets.QLabel(self.groupBox)
        self.label_dice.setGeometry(QtCore.QRect(20, 34, 110, 30))
        self.label_dice.setFont(self.times_font_14)
        self.label_dice.setText("Dice:")
        self.lineEdit_Dice = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_Dice.setGeometry(QtCore.QRect(20, 74, 110, 34))
        self.lineEdit_Dice.setFont(self.times_font_14)
        self.lineEdit_Dice.setAlignment(Qt.AlignCenter)
        self.lineEdit_Dice.setReadOnly(True)
        self.lineEdit_Dice.setStyleSheet("border: none; background: #f8fafc; border-radius: 8px; padding: 4px 6px; color: #0f172a;")
        self.lineEdit_Dice.setFrame(False)
        self.lineEdit_Dice.setFocusPolicy(Qt.NoFocus)
        self.label_jaccard = QtWidgets.QLabel(self.groupBox)
        self.label_jaccard.setGeometry(QtCore.QRect(20, 142, 110, 30))
        self.label_jaccard.setFont(self.times_font_14)
        self.label_jaccard.setText("Jaccard:")
        self.lineEdit_iou = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_iou.setGeometry(QtCore.QRect(20, 182, 110, 34))
        self.lineEdit_iou.setFont(self.times_font_14)
        self.lineEdit_iou.setAlignment(Qt.AlignCenter)
        self.lineEdit_iou.setReadOnly(True)
        self.lineEdit_iou.setStyleSheet("border: none; background: #f8fafc; border-radius: 8px; padding: 4px 6px; color: #0f172a;")
        self.lineEdit_iou.setFrame(False)
        self.lineEdit_iou.setFocusPolicy(Qt.NoFocus)
        MainWindow.setCentralWidget(self.centralwidget)
        MainWindow.setWindowTitle("肝脏肿瘤CT分割系统")
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setMinimumHeight(24)
        self.statusbar.setStyleSheet(
            "QStatusBar { border-top: 1px solid #c8d3df; background: #f8fafc; color: #334155; }"
        )
        MainWindow.setStatusBar(self.statusbar)

class MainWindow(QMainWindow):
    def __init__(self, api_base_url=None, auth_username=None, auth_password=None, auth_user_id=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.action_about.triggered.connect(self.show_about)
        self.ui.action_account.triggered.connect(self.open_account_dialog)
        self.init_slot()
        args = config.args
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = UNet(in_channel=1, out_channel=args.n_label, drop_rate=args.drop_rate, training=False)
        self.model = torch.nn.DataParallel(self.model)
        self.model = self.model.to(self.device)
        checkpoint = torch.load(f'{args.model_save}/best_model.pth', map_location=self.device)
        self.model.load_state_dict(checkpoint['net'])
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
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.auth_user_id = auth_user_id
        self.account_dialog = None
        self._init_status_bar()
        self._update_account_status()
        self._refresh_action_buttons()

    def show_about(self):
        html = (
            '<h3>肝脏肿瘤CT分割系统</h3>'
            f'<p><b>版本：</b>{__version__}</p>'
            '<p><b>作者：</b>于波</p>'
            '<p><b>机构：</b>桂林电子科技大学</p>'
            f'<p><b>编译日期：</b>2026-03-20</p>'
            '<hr>'
            '<p>本系统基于LDR-UNet模型构建，实现肝脏及肿瘤CT影像的自动分割、'
            '分割结果保存与评估等功能。</p>'
        )
        QMessageBox.about(self, '关于', html)

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
        self.ui.pushButton_segmentation.setEnabled(has_ct)
        self.ui.pushButton_segmentation_api.setEnabled(has_ct and not is_polling)
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
        path, _ = QFileDialog.getOpenFileName(None, '选择CT影像', './CT/ct', 'CT File (*.nii *.nii.gz)')
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
        path, _ = QFileDialog.getOpenFileName(None, '选择标注影像', './CT/label', 'Label File (*.nii *.nii.gz)')
        if not path:
            return
        self.label_data = self._load_volume_data(path, self.ui.lineEdit_label_path, self.ui.lineEdit_label_size)
        if self.ct_data is not None:
            self.display_slice()

    @staticmethod
    def _read_http_error(exc):
        return ApiClient.read_http_error(exc)

    def _submit_api_job(self, ct_path, endpoint="/jobs", auth_header=None):
        return self.api_client.submit_file_job(ct_path, endpoint=endpoint, auth_header=auth_header, timeout=120)

    def _query_api_job(self, job_id):
        return self.api_client.query_job(job_id, timeout=30)

    @staticmethod
    def _resolve_api_result_path(raw_path):
        return resolve_result_path(raw_path, base_dir=os.getcwd())

    def _start_api_polling(self, job_id, ct_path, endpoint):
        self.api_poll_context = {
            "job_id": job_id,
            "ct_path": ct_path,
            "endpoint": endpoint,
            "start_time": time.time(),
        }
        interval_ms = max(100, int(self.api_poll_interval_sec * 1000))
        self.api_poll_timer.setInterval(interval_ms)
        self.api_poll_timer.start()
        self._refresh_action_buttons()
        self._poll_api_job_once()

    def _stop_api_polling(self):
        if self.api_poll_timer.isActive():
            self.api_poll_timer.stop()
        self.api_poll_context = None
        self._refresh_action_buttons()

    def _poll_api_job_once(self):
        context = self.api_poll_context
        if not context:
            self._stop_api_polling()
            return

        job_id = context["job_id"]
        ct_path = context["ct_path"]
        endpoint = context["endpoint"]
        start_time = context["start_time"]

        if time.time() - start_time > self.api_timeout_sec:
            self._stop_api_polling()
            QMessageBox.warning(self, "警告", "任务轮询超时。", QMessageBox.Yes)
            return

        try:
            job = self._query_api_job(job_id)
        except urllib.error.HTTPError as exc:
            self._stop_api_polling()
            QMessageBox.critical(
                self, "错误", f"查询失败 (HTTP {exc.code})\n{self._read_http_error(exc)}", QMessageBox.Yes
            )
            return
        except urllib.error.URLError as exc:
            self._stop_api_polling()
            QMessageBox.critical(self, "错误", f"无法连接 API:\n{exc.reason}", QMessageBox.Yes)
            return
        except Exception as exc:
            self._stop_api_polling()
            QMessageBox.critical(self, "错误", f"查询失败:\n{exc}", QMessageBox.Yes)
            return

        status = job.get("status", "")
        if status in {"pending", "running"}:
            progress = min(95, 10 + int((time.time() - start_time) / self.api_timeout_sec * 90))
            self.ui.progressBar.setValue(progress)
            return

        self._stop_api_polling()

        if status == "succeeded":
            result_path = self._resolve_api_result_path(job.get("result_path"))
            elapsed_ms = job.get("elapsed_ms")
            if not result_path or not os.path.exists(result_path):
                QMessageBox.critical(self, "错误", f"任务成功但结果文件不存在:\n{result_path}", QMessageBox.Yes)
                return

            self.segmentation_path = result_path
            self.ct_name = os.path.basename(ct_path).split('-')[-1]
            nii_img = nib.load(self.segmentation_path)
            self.segmentation_data = nii_img.get_fdata()
            self.display_slice()
            self._refresh_action_buttons()
            self.ui.progressBar.setValue(100)
            mode_text = "me/jobs" if endpoint == "/me/jobs" else "jobs"
            self._show_segmentation_success(mode_text, job_id, elapsed_ms)
            return

        error_msg = job.get("error") or "未知错误"
        elapsed_ms = job.get("elapsed_ms")
        self.ui.progressBar.setValue(0)
        QMessageBox.critical(
            self,
            "错误",
            f"API 分割失败\n任务ID: {job_id}\n耗时: {self._format_elapsed_seconds(elapsed_ms)} s\n错误: {error_msg}",
            QMessageBox.Yes,
        )

    def segmentation_api(self):
        if self.api_poll_context is not None:
            QMessageBox.information(self, "提示", "已有 API 任务在运行，请稍候。", QMessageBox.Yes)
            return

        ct_path = self.ui.lineEdit_CT_path.text().strip()
        if not ct_path:
            QMessageBox.information(self, "提示", "请先加载 CT 文件。", QMessageBox.Yes)
            return
        if not os.path.exists(ct_path):
            QMessageBox.critical(self, "错误", f"CT 文件不存在:\n{ct_path}", QMessageBox.Yes)
            return

        self.ui.lineEdit_Dice.setText("")
        self.ui.lineEdit_iou.setText("")
        self.ui.progressBar.setValue(5)

        if not self.is_user_logged_in():
            QMessageBox.warning(self, "警告", "请先重启应用并登录。", QMessageBox.Yes)
            return

        endpoint = "/me/jobs"
        auth_header = self._auth_header()

        try:
            submit_resp = self._submit_api_job(ct_path, endpoint=endpoint, auth_header=auth_header)
            job_id = submit_resp.get("job_id")
            if not job_id:
                raise RuntimeError(f"Invalid {endpoint} response: {submit_resp}")
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                self.api_logout_user()
                QMessageBox.warning(self, "警告", "登录已过期，请重启应用后重新登录。", QMessageBox.Yes)
                return
            QMessageBox.critical(
                self, "错误", f"提交失败 (HTTP {exc.code})\n{self._read_http_error(exc)}", QMessageBox.Yes
            )
            return
        except urllib.error.URLError as exc:
            QMessageBox.critical(self, "错误", f"无法连接 API:\n{exc.reason}", QMessageBox.Yes)
            return
        except Exception as exc:
            QMessageBox.critical(self, "错误", f"提交失败:\n{exc}", QMessageBox.Yes)
            return

        self.ui.progressBar.setValue(10)
        self._start_api_polling(job_id, ct_path, endpoint)

    def segmentation(self):
        if not self.ui.lineEdit_CT_path.text():
            QMessageBox.information(self, "提示", "请先选择CT", QMessageBox.Yes)
            return
        start_time = time.time()
        args = config.args
        self.result_save_path = f'{args.log_save}/result'
        if not os.path.exists(self.result_save_path):
            os.mkdir(self.result_save_path)
        ct_path = self.ui.lineEdit_CT_path.text()
        datasets = self.Test_Datasets(ct_path, None, args)
        for ct_dataset, self.ct_name in datasets:
            _, pred_ct = self.predict(self.model, ct_dataset, args)
            self.segmentation_path = os.path.join(self.result_save_path, f'result-{self.ct_name}')
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
                output = torch.nn.functional.interpolate(output, scale_factor=(
                    1 / args.z_down_scale, 1 / args.xy_down_scale, 1 / args.xy_down_scale), mode='trilinear',
                                                         align_corners=False)
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
            yield Test_DataSet(ct_file, label_file, args=args), ct_file.split('-')[-1]

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
            suffix = '.nii' if selected_filter.startswith("NIFTI 文件") else '.nii.gz'
            base = folder_path
            while True:
                lower = base.lower()
                if lower.endswith('.nii.gz'):
                    base = base[:-7]
                elif lower.endswith('.nii'):
                    base = base[:-4]
                elif lower.endswith('.gz'):
                    base = base[:-3]
                else:
                    break
            folder_path = base + suffix
            break
        try:
            if folder_path.lower().endswith('.nii.gz'):
                import gzip
                with open(src_file, 'rb') as f_in, gzip.open(folder_path, 'wb') as f_out:
                    while True:
                        chunk = f_in.read(1024 * 1024)
                        if not chunk:
                            break
                        f_out.write(chunk)
            else:
                shutil.copy(src_file, folder_path)
            settings.setValue("last_save_path", os.path.dirname(folder_path))
            QMessageBox.information(self, "提示", "保存成功", QMessageBox.Yes)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}", QMessageBox.Yes)

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

