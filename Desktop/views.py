import urllib.error
from datetime import datetime, timezone

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QMessageBox

from Desktop.api_client import ApiClient


class LoginGateDialog(QtWidgets.QDialog):
    def __init__(self, default_api_base):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("肝脏肿瘤CT分割系统")
        self.setFixedSize(600, 260)
        self.setFont(QFont("Microsoft YaHei UI", 10))

        self.api_base_url = (default_api_base or "http://127.0.0.1:8000").rstrip("/")
        self.api_client = ApiClient(self.api_base_url)
        self.username = None
        self.password = None
        self.user_id = None
        self.settings = QSettings("LiverSeg", "LoginGate")

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

        saved_api = self.settings.value("api_base_url", self.api_base_url, type=str)
        saved_username = ""

        self.edit_api = QtWidgets.QLineEdit(saved_api)
        self.edit_username = QtWidgets.QLineEdit(saved_username)
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

        self.btn_register.clicked.connect(self._on_register)
        self.btn_login.clicked.connect(self._on_login)
        self.edit_password.returnPressed.connect(self._on_login)
        self.edit_username.returnPressed.connect(self._on_login)
        self.edit_api.returnPressed.connect(self._on_login)

    @staticmethod
    def _read_http_error(exc):
        return ApiClient.read_http_error(exc)

    def _set_busy(self, busy):
        self.btn_login.setEnabled(not busy)
        self.btn_register.setEnabled(not busy)
        if busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    @staticmethod
    def _is_valid_base_url(base):
        return base.startswith("http://") or base.startswith("https://")

    def _persist_inputs(self, base, username):
        self.settings.setValue("api_base_url", base)

    def _collect_inputs(self):
        base = self.edit_api.text().strip().rstrip("/")
        if not base:
            base = "http://127.0.0.1:8000"
        username = self.edit_username.text().strip()
        password = self.edit_password.text()

        if not self._is_valid_base_url(base):
            raise RuntimeError("API 地址必须以 http:// 或 https:// 开头")
        if not username:
            raise RuntimeError("请输入账号")
        if not password:
            raise RuntimeError("请输入密码")

        self.api_base_url = base
        self.api_client.set_base_url(base)
        return base, username, password

    def _request_json(self, method, path, payload):
        return self.api_client.request_json(method, path, payload=payload, timeout=20)

    def _on_register(self):
        self._set_busy(True)
        try:
            base, username, password = self._collect_inputs()
            data = self._request_json("POST", "/register", {"username": username, "password": password})
            self._persist_inputs(base, username)
            QMessageBox.information(self, "提示", f"注册成功: {data.get('username', username)}，可直接登录", QMessageBox.Yes)
        except urllib.error.HTTPError as exc:
            QMessageBox.critical(
                self,
                "错误",
                f"注册失败: HTTP {exc.code}\n{self._read_http_error(exc)}",
                QMessageBox.Yes,
            )
        except urllib.error.URLError as exc:
            QMessageBox.critical(self, "错误", f"注册失败: 无法连接 API\n{exc.reason}", QMessageBox.Yes)
        except Exception as exc:
            QMessageBox.critical(self, "错误", f"注册失败: {exc}", QMessageBox.Yes)
        finally:
            self._set_busy(False)

    def _on_login(self):
        self._set_busy(True)
        try:
            base, username, password = self._collect_inputs()
            data = self._request_json("POST", "/login", {"username": username, "password": password})
            self.username = username
            self.password = password
            self.user_id = data.get("id")
            self._persist_inputs(base, username)
            self.accept()
        except urllib.error.HTTPError as exc:
            QMessageBox.critical(
                self,
                "错误",
                f"登录失败: HTTP {exc.code}\n{self._read_http_error(exc)}",
                QMessageBox.Yes,
            )
        except urllib.error.URLError as exc:
            QMessageBox.critical(self, "错误", f"登录失败: 无法连接 API\n{exc.reason}", QMessageBox.Yes)
        except Exception as exc:
            QMessageBox.critical(self, "错误", f"登录失败: {exc}", QMessageBox.Yes)
        finally:
            self._set_busy(False)


class AccountDialog(QtWidgets.QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.main = main_window
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

        self.edit_api_base = QtWidgets.QLineEdit(self.main.api_base_url)
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

        self.btn_copy_api.clicked.connect(lambda: self._copy_to_clipboard(self.edit_api_base.text(), "api"))
        self.btn_copy_username.clicked.connect(lambda: self._copy_to_clipboard(self.view_username.text(), "username"))
        self.btn_copy_password.clicked.connect(lambda: self._copy_to_clipboard(self.view_password.text(), "password"))
        self.btn_refresh_jobs.clicked.connect(self._on_refresh_jobs)

        self._update_view()
        self.edit_api_base.deselect()
        self.view_username.deselect()
        self.view_password.deselect()
        if self.btn_refresh_jobs.isEnabled():
            self.btn_refresh_jobs.setFocus(Qt.OtherFocusReason)
        else:
            self.btn_copy_api.setFocus(Qt.OtherFocusReason)

    def _sync_api_base_url(self):
        base_url = self.edit_api_base.text().strip()
        self.main.set_api_base_url(base_url)
        self.edit_api_base.setText(self.main.api_base_url)

    def _set_status(self, text, error=False):
        if error:
            style = (
                "QLabel {color:#b91c1c; background:#fef2f2; border:1px solid #fecaca; border-radius:6px; padding:4px 8px;}"
            )
        else:
            style = (
                "QLabel {color:#065f46; background:#ecfdf5; border:1px solid #a7f3d0; border-radius:6px; padding:4px 8px;}"
            )
        self.label_status.setStyleSheet(style)
        self.label_status.setText(text)

    @staticmethod
    def _format_local_time(utc_text):
        text = str(utc_text or "").strip()
        if not text:
            return "-"
        try:
            if text.endswith("Z"):
                dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(text)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return text

    @staticmethod
    def _format_elapsed_seconds(elapsed_ms):
        try:
            if elapsed_ms is None:
                return "-"
            return f"{float(elapsed_ms) / 1000.0:.2f}"
        except (TypeError, ValueError):
            return "-"

    def _copy_to_clipboard(self, value, field_name):
        QApplication.clipboard().setText(value or "")
        if field_name == "username":
            self._set_status("账号已复制")
        elif field_name == "password":
            self._set_status("密码已复制")
        elif field_name == "api":
            self._set_status("API 地址已复制")
        else:
            self._set_status("已复制")

    def _update_view(self):
        self.edit_api_base.setText(self.main.api_base_url)
        self.view_username.setText(self.main.auth_username or "")
        self.view_password.setText(self.main.auth_password or "")
        if self.main.is_user_logged_in():
            self._set_status(f"已登录: {self.main.auth_username}")
            self.btn_refresh_jobs.setEnabled(True)
        else:
            self._set_status("未登录", error=True)
            self.btn_refresh_jobs.setEnabled(False)

    def _render_jobs(self, items):
        self.jobs_table.clearContents()
        self.jobs_table.clearSpans()

        if not items:
            self.jobs_table.setRowCount(1)
            empty_item = QtWidgets.QTableWidgetItem("暂无任务记录")
            empty_item.setFlags(Qt.ItemIsEnabled)
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.jobs_table.setItem(0, 0, empty_item)
            self.jobs_table.setSpan(0, 0, 1, self.jobs_table.columnCount())
            return

        status_map = {
            "succeeded": "成功",
            "failed": "失败",
            "running": "运行中",
            "pending": "排队中",
        }
        self.jobs_table.setRowCount(len(items))
        for row, item in enumerate(items):
            values = [
                self._format_local_time(item.get("created_at")),
                str(item.get("job_id", "-")),
                status_map.get(str(item.get("status", "-")), str(item.get("status", "-"))),
                self._format_elapsed_seconds(item.get("elapsed_ms")),
            ]
            for col, value in enumerate(values):
                cell = QtWidgets.QTableWidgetItem(value)
                if col in (0, 2, 3):
                    cell.setTextAlignment(Qt.AlignCenter)
                self.jobs_table.setItem(row, col, cell)

    def _on_refresh_jobs(self):
        self._sync_api_base_url()
        if not self.main.is_user_logged_in():
            self._set_status("请先重新启动程序登录", error=True)
            return
        try:
            payload = self.main.api_list_my_jobs(limit=30)
            items = payload.get("items", [])
            self._render_jobs(items)
            self._set_status(f"任务已刷新: {len(items)} 条")
        except Exception as exc:
            self._set_status(f"刷新失败: {exc}", error=True)
            QMessageBox.critical(self, "错误", f"刷新任务失败:\n{exc}", QMessageBox.Yes)
