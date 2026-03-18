import config
from Model.Model import UNet
import os
import sys
import torch
import shutil
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from scipy import ndimage
from torch.utils.data import Dataset
from PyQt5.QtCore import Qt, QSettings
from torch.utils.data import DataLoader
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox


__version__ = '1.0.0'


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1038, 666)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f5f5f5"))
        MainWindow.setPalette(palette)
        menubar = MainWindow.menuBar()
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
            QPushButton {border-radius: 10px; background-color: #e0e0e0; padding: 5px;}
            QPushButton:hover {background-color: #d0d0d0;}
        """
        self.lineedit_style = "border: 1px solid #ccc; background-color: #fff; border-radius: 5px; padding: 5px;"
        self.label_style = "border: 1px solid #ccc; background-color: #fff;"
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
        self.pushButton_segmentation.setGeometry(QtCore.QRect(858, 50, 150, 50))
        self.pushButton_segmentation.setFont(self.kai_font_14)
        self.pushButton_segmentation.setText("点击分割")
        self.pushButton_segmentation.setStyleSheet(self.button_style)
        self.pushButton_segmentation.setToolTip("执行肝脏肿瘤CT分割")
        self.pushButton_save = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_save.setGeometry(QtCore.QRect(858, 130, 150, 50))
        self.pushButton_save.setFont(self.kai_font_14)
        self.pushButton_save.setText("点击保存")
        self.pushButton_save.setStyleSheet(self.button_style)
        self.pushButton_save.setToolTip("保存分割结果")
        self.pushButton_info = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_info.setGeometry(QtCore.QRect(858, 210, 150, 50))
        self.pushButton_info.setFont(self.kai_font_14)
        self.pushButton_info.setText("点击评价")
        self.pushButton_info.setStyleSheet(self.button_style)
        self.pushButton_info.setToolTip("显示分割指标")
        self.label_metrics_title = QtWidgets.QLabel(self.centralwidget)
        self.label_metrics_title.setGeometry(QtCore.QRect(858, 320, 150, 30))
        self.label_metrics_title.setFont(self.kai_font_14)
        self.label_metrics_title.setText("分割指标")
        self.label_metrics_title.setAlignment(Qt.AlignCenter)
        self.label_metrics_title.setStyleSheet("background: transparent;")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(858, 350, 150, 226))
        self.groupBox.setFont(self.kai_font_14)
        self.groupBox.setTitle("")
        self.groupBox.setAlignment(Qt.AlignCenter)
        self.groupBox.setStyleSheet(""" QGroupBox { background:#fff; border:1px solid #ccc; margin-top:0px; } """)
        self.label_dice = QtWidgets.QLabel(self.groupBox)
        self.label_dice.setGeometry(QtCore.QRect(25, 28, 100, 30))
        self.label_dice.setFont(self.times_font_14)
        self.label_dice.setText("Dice:")
        self.lineEdit_Dice = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_Dice.setGeometry(QtCore.QRect(25, 68, 100, 30))
        self.lineEdit_Dice.setFont(self.times_font_14)
        self.lineEdit_Dice.setAlignment(Qt.AlignCenter)
        self.lineEdit_Dice.setReadOnly(True)
        self.lineEdit_Dice.setStyleSheet(self.lineedit_style)
        self.label_jaccard = QtWidgets.QLabel(self.groupBox)
        self.label_jaccard.setGeometry(QtCore.QRect(25, 128, 100, 30))
        self.label_jaccard.setFont(self.times_font_14)
        self.label_jaccard.setText("Jaccard:")
        self.lineEdit_iou = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_iou.setGeometry(QtCore.QRect(25, 168, 100, 30))
        self.lineEdit_iou.setFont(self.times_font_14)
        self.lineEdit_iou.setAlignment(Qt.AlignCenter)
        self.lineEdit_iou.setReadOnly(True)
        self.lineEdit_iou.setStyleSheet(self.lineedit_style)
        MainWindow.setCentralWidget(self.centralwidget)
        MainWindow.setWindowTitle("肝脏肿瘤CT分割系统")
        MainWindow.statusBar()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.action_about.triggered.connect(self.show_about)
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

    def show_about(self):
        html = (
            '<h3>肝脏肿瘤CT分割系统</h3>'
            f'<p><b>版本：</b>{__version__}</p>'
            '<p><b>作者：</b>于波</p>'
            '<p><b>机构：</b>桂林电子科技大学</p>'
            f'<p><b>编译日期：</b>2025-05-20</p>'
            '<hr>'
            '<p>本系统基于LDR-UNet模型构建，实现肝脏及肿瘤CT影像的自动分割、'
            '分割结果保存与评估等功能。</p>'
        )
        QMessageBox.about(self, '关于', html)

    def init_slot(self):
        self.ui.pushButton_CT.clicked.connect(self.load_CT)
        self.ui.pushButton_label.clicked.connect(self.load_label)
        self.ui.pushButton_segmentation.clicked.connect(self.segmentation)
        self.ui.pushButton_save.clicked.connect(self.save)
        self.ui.pushButton_info.clicked.connect(self.info)
        self.ui.pushButton_next.clicked.connect(self.next_slice)
        self.ui.pushButton_previous.clicked.connect(self.previous_slice)

    def load_CT(self):
        path, _ = QFileDialog.getOpenFileName(None, '选择CT影像', './CT/ct', 'CT File (*.nii *.nii.gz)')
        if not path:
            return
        self.ui.lineEdit_Dice.setText("")
        self.ui.lineEdit_iou.setText("")
        self.ui.progressBar.setValue(0)
        self.ui.lineEdit_CT_path.setText(path)
        file_size = os.path.getsize(path)
        size_in_mb = f"{file_size / (1024 * 1024):.2f} MB"
        self.ui.lineEdit_Ct_size.setText(size_in_mb)
        nii_img = nib.load(path)
        self.ct_data = nii_img.get_fdata()
        self.current_slice_index = self.ct_data.shape[2] // 2
        self.segmentation_data = None
        self.display_slice()

    def load_label(self):
        path, _ = QFileDialog.getOpenFileName(None, '选择标注影像', './CT/label', 'Label File (*.nii *.nii.gz)')
        if not path:
            return
        self.ui.lineEdit_label_path.setText(path)
        file_size = os.path.getsize(path)
        fm_size_in_mb = f"{file_size / (1024 * 1024):.2f} MB"
        self.ui.lineEdit_label_size.setText(fm_size_in_mb)
        nii_img = nib.load(path)
        self.label_data = nii_img.get_fdata()
        if self.ct_data is not None:
            self.display_slice()

    def segmentation(self):
        if not self.ui.lineEdit_CT_path.text():
            QMessageBox.information(self, "提示", "请先选择CT", QMessageBox.Yes)
            return
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
        QMessageBox.information(self, "提示", "分割成功", QMessageBox.Yes)

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

    def display_slice(self):
        if self.ct_data is not None:
            slice_data = self.ct_data[:, :, self.current_slice_index]
            slice_data = (slice_data - slice_data.min()) / (slice_data.max() - slice_data.min()) * 255
            slice_data = slice_data.astype(np.uint8)
            height, width = slice_data.shape
            bytes_per_line = width
            qimage = QImage(slice_data.tobytes(), width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label_size = self.ui.label_ct.size()
            scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.ui.label_ct.setPixmap(scaled_pixmap)
        if self.label_data is not None:
            slice_data = self.label_data[:, :, self.current_slice_index]
            slice_data = (slice_data - slice_data.min()) / (slice_data.max() - slice_data.min()) * 255
            slice_data = slice_data.astype(np.uint8)
            height, width = slice_data.shape
            bytes_per_line = width
            qimage = QImage(slice_data.tobytes(), width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label_size = self.ui.label_label.size()
            scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.ui.label_label.setPixmap(scaled_pixmap)
        if self.segmentation_data is not None:
            slice_data = self.segmentation_data[:, :, self.current_slice_index]
            slice_data = (slice_data - slice_data.min()) / (slice_data.max() - slice_data.min()) * 255
            slice_data = slice_data.astype(np.uint8)
            height, width = slice_data.shape
            bytes_per_line = width
            qimage = QImage(slice_data.tobytes(), width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label_size = self.ui.label_segmentation.size()
            scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.ui.label_segmentation.setPixmap(scaled_pixmap)
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


class Test_DataSet(Dataset):
    def __init__(self, ct_path, label_path, args):
        self.n_label = args.n_label
        self.cut_size = args.tc_size
        self.cut_stride = args.tc_stride
        self.ct = sitk.ReadImage(ct_path, sitk.sitkInt16)
        self.ct_np = sitk.GetArrayFromImage(self.ct)
        self.ori_shape = self.ct_np.shape
        self.ct_np = ndimage.zoom(self.ct_np, (args.z_down_scale, args.xy_down_scale, args.xy_down_scale), order=3)
        self.resized_shape = self.ct_np.shape
        self.ct_np[self.ct_np > args.upper] = args.upper
        self.ct_np[self.ct_np < args.lower] = args.lower
        self.ct_np = (self.ct_np + 100) / 400
        self.ct_np = self.ct_np.astype(np.float32)
        self.ct_np = self.padding_ct(self.ct_np, self.cut_size, self.cut_stride)
        self.padding_shape = self.ct_np.shape
        self.ct_np = self.extract_ordered_overlap(self.ct_np, self.cut_size, self.cut_stride)
        self.label = None
        if label_path:
            self.seg = sitk.ReadImage(label_path, sitk.sitkInt8)
            self.label_np = sitk.GetArrayFromImage(self.seg)
            if self.n_label == 2:
                self.label_np[self.label_np > 0] = 1
            self.label = torch.from_numpy(np.expand_dims(self.label_np, axis=0)).long()
        self.result = None

    def __getitem__(self, index):
        data = torch.from_numpy(self.ct_np[index])
        data = torch.FloatTensor(data).unsqueeze(0)
        return data

    def __len__(self):
        return len(self.ct_np)

    def update_result(self, tensor):
        if self.result is not None:
            self.result = torch.cat((self.result, tensor), dim=0)
        else:
            self.result = tensor

    def recompone_result(self):
        patch_s = self.result.shape[2]
        N_patches_ct = (self.padding_shape[0] - patch_s) // self.cut_stride + 1
        assert (self.result.shape[0] == N_patches_ct)
        full_prob = torch.zeros((self.n_label, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))
        full_sum = torch.zeros((self.n_label, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))
        for s in range(N_patches_ct):
            full_prob[:, s * self.cut_stride:s * self.cut_stride + patch_s] += self.result[s]
            full_sum[:, s * self.cut_stride:s * self.cut_stride + patch_s] += 1
        assert (torch.min(full_sum) >= 1.0)
        final_avg = full_prob / full_sum
        assert (torch.max(final_avg) <= 1.0)
        assert (torch.min(final_avg) >= 0.0)
        ct = final_avg[:, :self.ori_shape[0], :self.ori_shape[1], :self.ori_shape[2]]
        return ct.unsqueeze(0)

    def padding_ct(self, ct, size, stride):
        assert (len(ct.shape) == 3)
        ct_s, ct_h, ct_w = ct.shape
        leftover_s = (ct_s - size) % stride
        if (leftover_s != 0):
            s = ct_s + (stride - leftover_s)
        else:
            s = ct_s
        tmp_full_imgs = np.zeros((s, ct_h, ct_w), dtype=np.float32)
        tmp_full_imgs[:ct_s] = ct
        return tmp_full_imgs

    def extract_ordered_overlap(self, ct, size, stride):
        ct_s, ct_h, ct_w = ct.shape
        assert (ct_s - size) % stride == 0
        N_patches_ct = (ct_s - size) // stride + 1
        patches = np.empty((N_patches_ct, size, ct_h, ct_w), dtype=np.float32)
        for s in range(N_patches_ct):
            patch = ct[s * stride: s * stride + size]
            patches[s] = patch
        return patches

class MetricsCalculator(object):
    def __init__(self, class_num):
        self.class_num = class_num
        self.reset()

    def reset(self):
        self.dice_sum = np.asarray([0] * self.class_num, dtype='float64')
        self.iou_sum = np.asarray([0] * self.class_num, dtype='float64')
        self.count = 0

    def update(self, logits, targets):
        dice, iou = self.get_metrics(logits, targets)
        self.dice_sum += dice
        self.iou_sum += iou
        self.count += 1

    def get_averages(self):
        dice_avg = np.around(self.dice_sum / self.count, 4)
        iou_avg = np.around(self.iou_sum / self.count, 4)
        return dice_avg, iou_avg

    def get_metrics(self, logits, targets):
        dices = []
        ious = []
        for class_index in range(targets.size()[1]):
            inter = torch.sum(logits[:, class_index, :, :, :] * targets[:, class_index, :, :, :])
            union = torch.sum(logits[:, class_index, :, :, :]) + torch.sum(targets[:, class_index, :, :, :])
            dice = (2. * inter) / (union + 0.0001)
            iou = inter / (union - inter + 0.0001)
            dices.append(dice.item())
            ious.append(iou.item())
        return np.asarray(dices), np.asarray(ious)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())