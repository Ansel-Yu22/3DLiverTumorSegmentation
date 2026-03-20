from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette

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

