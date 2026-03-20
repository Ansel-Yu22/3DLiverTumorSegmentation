from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LoginGateDialogUiMixin:
    def setup_login_ui(self, api_base_url):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("肝脏肿瘤CT分割系统")
        self.setFixedSize(600, 260)
        self.setFont(QFont("Microsoft YaHei UI", 10))

        label_font = QFont("Microsoft YaHei UI", 11)
        label_font.setWeight(QFont.DemiBold)
        input_font = QFont("Microsoft YaHei UI", 11)
        button_font = QFont("Microsoft YaHei UI", 12)
        button_font.setWeight(QFont.DemiBold)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(14, 16, 14, 16)
        root.setSpacing(10)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(18)

        self.edit_api = QtWidgets.QLineEdit(api_base_url)
        self.edit_username = QtWidgets.QLineEdit("")
        self.edit_password = QtWidgets.QLineEdit()
        self.edit_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.label_api = QtWidgets.QLabel("API 地址")
        self.label_account = QtWidgets.QLabel("账号")
        self.label_password = QtWidgets.QLabel("密码")

        self.edit_api.setPlaceholderText("http://127.0.0.1:8000")
        self.edit_username.setPlaceholderText("账号")
        self.edit_password.setPlaceholderText("密码")
        self.edit_api.setClearButtonEnabled(False)
        self.edit_username.setClearButtonEnabled(False)
        self.edit_password.setClearButtonEnabled(False)

        edit_style = (
            "QLineEdit {border:1px solid #cbd5e1; border-radius:6px; padding:6px 8px; background:white;}"
            "QLineEdit:focus {border:1px solid #2563eb;}"
        )
        for edit in (self.edit_api, self.edit_username, self.edit_password):
            edit.setMinimumHeight(32)
            edit.setStyleSheet(edit_style)
            edit.setFont(input_font)

        self.edit_username.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.edit_password.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        for label in (self.label_api, self.label_account, self.label_password):
            label.setFont(label_font)

        form.addRow(self.label_api, self.edit_api)
        form.addRow(self.label_account, self.edit_username)
        form.addRow(self.label_password, self.edit_password)
        root.addLayout(form)
        root.addSpacing(8)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)

        self.btn_register = QtWidgets.QPushButton("注册")
        self.btn_login = QtWidgets.QPushButton("登录")
        self.btn_login.setDefault(True)
        self.btn_login.setAutoDefault(True)

        uniform_button_style = (
            "QPushButton {background:#2563eb; color:white; border:none; border-radius:6px; padding:6px 10px;}"
            "QPushButton:hover {background:#1d4ed8;}"
            "QPushButton:disabled {background:#93c5fd;}"
        )
        self.btn_login.setStyleSheet(uniform_button_style)
        self.btn_register.setStyleSheet(uniform_button_style)
        for button in (self.btn_register, self.btn_login):
            button.setFixedSize(200, 36)
            button.setFont(button_font)

        row.addStretch(1)
        row.addWidget(self.btn_register)
        row.addWidget(self.btn_login)
        row.addStretch(1)
        root.addLayout(row)
        root.addSpacing(6)


class AccountDialogUiMixin:
    def setup_account_ui(self, api_base_url):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("账号中心")
        self.setMinimumSize(760, 560)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)

        readonly_style = (
            "QLineEdit {border:1px solid #cbd5e1; border-radius:6px; padding:6px 8px; background:#f8fafc; color:#0f172a;}"
        )
        primary_button_style = (
            "QPushButton {background:#2563eb; color:white; border:none; border-radius:6px; padding:6px 12px;}"
            "QPushButton:hover {background:#1d4ed8;}"
            "QPushButton:disabled {background:#93c5fd; color:#e2e8f0;}"
        )
        secondary_button_style = (
            "QPushButton {background:#e2e8f0; color:#0f172a; border:1px solid #cbd5e1; border-radius:6px; padding:6px 10px;}"
            "QPushButton:hover {background:#dbe5f1;}"
            "QPushButton:disabled {background:#f1f5f9; color:#94a3b8; border-color:#e2e8f0;}"
        )
        row_label_style = "color:#0f172a; padding-right:2px;"

        def make_row_label(text):
            label = QtWidgets.QLabel(text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setMinimumHeight(36)
            label.setStyleSheet(row_label_style)
            return label

        self.edit_api_base = QtWidgets.QLineEdit(api_base_url)
        self.edit_api_base.setPlaceholderText("http://127.0.0.1:8000")
        self.edit_api_base.setReadOnly(True)
        self.edit_api_base.setFocusPolicy(Qt.NoFocus)
        self.edit_api_base.setStyleSheet(readonly_style)
        self.edit_api_base.setMinimumHeight(34)
        self.btn_copy_api = QtWidgets.QPushButton("复制")
        self.btn_copy_api.setStyleSheet(secondary_button_style)
        self.btn_copy_api.setFixedWidth(92)
        self.btn_copy_api.setFixedHeight(34)
        api_row = QtWidgets.QWidget()
        api_row.setMinimumHeight(36)
        api_layout = QtWidgets.QHBoxLayout(api_row)
        api_layout.setContentsMargins(0, 0, 0, 0)
        api_layout.setSpacing(8)
        api_layout.setAlignment(Qt.AlignVCenter)
        api_layout.addWidget(self.edit_api_base, 1)
        api_layout.addWidget(self.btn_copy_api)
        form.addRow(make_row_label("API 地址"), api_row)

        self.view_username = QtWidgets.QLineEdit()
        self.view_username.setReadOnly(True)
        self.view_username.setFocusPolicy(Qt.NoFocus)
        self.view_username.setStyleSheet(readonly_style)
        self.view_username.setMinimumHeight(34)
        self.btn_copy_username = QtWidgets.QPushButton("复制")
        self.btn_copy_username.setStyleSheet(secondary_button_style)
        self.btn_copy_username.setFixedWidth(92)
        self.btn_copy_username.setFixedHeight(34)
        username_row = QtWidgets.QWidget()
        username_row.setMinimumHeight(36)
        username_layout = QtWidgets.QHBoxLayout(username_row)
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.setSpacing(8)
        username_layout.setAlignment(Qt.AlignVCenter)
        username_layout.addWidget(self.view_username, 1)
        username_layout.addWidget(self.btn_copy_username)
        form.addRow(make_row_label("当前账号"), username_row)

        self.view_password = QtWidgets.QLineEdit()
        self.view_password.setReadOnly(True)
        self.view_password.setFocusPolicy(Qt.NoFocus)
        self.view_password.setStyleSheet(readonly_style)
        self.view_password.setMinimumHeight(34)
        self.btn_copy_password = QtWidgets.QPushButton("复制")
        self.btn_copy_password.setStyleSheet(secondary_button_style)
        self.btn_copy_password.setFixedWidth(92)
        self.btn_copy_password.setFixedHeight(34)
        password_row = QtWidgets.QWidget()
        password_row.setMinimumHeight(36)
        password_layout = QtWidgets.QHBoxLayout(password_row)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(8)
        password_layout.setAlignment(Qt.AlignVCenter)
        password_layout.addWidget(self.view_password, 1)
        password_layout.addWidget(self.btn_copy_password)
        form.addRow(make_row_label("当前密码"), password_row)
        root.addLayout(form)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        self.btn_refresh_jobs = QtWidgets.QPushButton("刷新任务")
        self.btn_refresh_jobs.setStyleSheet(primary_button_style)
        self.btn_refresh_jobs.setMinimumHeight(36)
        row.addWidget(self.btn_refresh_jobs)
        root.addLayout(row)

        self.label_status = QtWidgets.QLabel("")
        self.label_status.setMinimumHeight(30)
        self.label_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_status.setContentsMargins(10, 0, 10, 0)
        root.addWidget(self.label_status)

        self.jobs_table = QtWidgets.QTableWidget(0, 4)
        self.jobs_table.setHorizontalHeaderLabels(["创建时间", "任务ID", "状态", "耗时(s)"])
        self.jobs_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.jobs_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.jobs_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.jobs_table.setWordWrap(False)
        self.jobs_table.setAlternatingRowColors(True)
        self.jobs_table.verticalHeader().setVisible(False)
        self.jobs_table.verticalHeader().setDefaultSectionSize(30)
        header = self.jobs_table.horizontalHeader()
        header.setHighlightSections(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.jobs_table.setStyleSheet(
            "QTableWidget {border:1px solid #cbd5e1; border-radius:6px; background:white; gridline-color:#e2e8f0;}"
            "QHeaderView::section {background:#f8fafc; border:0px; border-bottom:1px solid #e2e8f0; padding:6px; color:#334155;}"
            "QTableWidget::item {padding:4px;}"
            "QTableWidget::item:selected {background:#dbeafe; color:#0f172a;}"
        )
        root.addWidget(self.jobs_table, 1)
