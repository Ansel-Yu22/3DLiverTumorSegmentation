from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from desktop.ui import ui_style as S
from desktop.ui import ui_text as T


class LoginDialogUiMixin:
    def setup_login_ui(self, api_base_url):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(T.APP_TITLE)
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
        self.label_api = QtWidgets.QLabel(T.LABEL_API)
        self.label_account = QtWidgets.QLabel(T.LABEL_ACCOUNT)
        self.label_password = QtWidgets.QLabel(T.LABEL_PASSWORD)

        self.edit_api.setPlaceholderText(T.PLACEHOLDER_API)
        self.edit_username.setPlaceholderText(T.PLACEHOLDER_ACCOUNT)
        self.edit_password.setPlaceholderText(T.PLACEHOLDER_PASSWORD)
        self.edit_api.setClearButtonEnabled(False)
        self.edit_username.setClearButtonEnabled(False)
        self.edit_password.setClearButtonEnabled(False)

        for edit in (self.edit_api, self.edit_username, self.edit_password):
            edit.setMinimumHeight(32)
            edit.setStyleSheet(S.LOGIN_EDIT_STYLE)
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

        self.btn_register = QtWidgets.QPushButton(T.BUTTON_REGISTER)
        self.btn_login = QtWidgets.QPushButton(T.BUTTON_LOGIN)
        self.btn_login.setDefault(True)
        self.btn_login.setAutoDefault(True)

        self.btn_login.setStyleSheet(S.LOGIN_BUTTON_STYLE)
        self.btn_register.setStyleSheet(S.LOGIN_BUTTON_STYLE)
        for button in (self.btn_register, self.btn_login):
            button.setFixedSize(200, 36)
            button.setFont(button_font)

        row.addStretch(1)
        row.addWidget(self.btn_register)
        row.addWidget(self.btn_login)
        row.addStretch(1)
        root.addLayout(row)
        root.addSpacing(6)

