import urllib.error

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox

from desktop.api_client import ApiClient


class LoginGateDialog(QtWidgets.QDialog):
    def __init__(self, default_api_base):
        super().__init__()
        self.setWindowTitle("登录 / 注册")
        self.setMinimumSize(460, 260)
        self.api_base_url = (default_api_base or "http://127.0.0.1:8000").rstrip("/")
        self.api_client = ApiClient(self.api_base_url)
        self.username = None
        self.password = None
        self.user_id = None

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        form = QtWidgets.QFormLayout()
        self.edit_api = QtWidgets.QLineEdit(self.api_base_url)
        self.edit_username = QtWidgets.QLineEdit()
        self.edit_password = QtWidgets.QLineEdit()
        self.edit_password.setEchoMode(QtWidgets.QLineEdit.Password)

        self.edit_api.setPlaceholderText("http://127.0.0.1:8000")
        self.edit_username.setPlaceholderText("username")
        self.edit_password.setPlaceholderText("password")

        form.addRow("API Base URL", self.edit_api)
        form.addRow("用户名", self.edit_username)
        form.addRow("密码", self.edit_password)
        root.addLayout(form)

        row = QtWidgets.QHBoxLayout()
        self.btn_register = QtWidgets.QPushButton("注册")
        self.btn_login = QtWidgets.QPushButton("登录并进入系统")
        self.btn_cancel = QtWidgets.QPushButton("退出")
        row.addWidget(self.btn_register)
        row.addWidget(self.btn_login)
        row.addWidget(self.btn_cancel)
        root.addLayout(row)

        self.label_status = QtWidgets.QLabel("请输入账号信息")
        self.label_status.setStyleSheet("color:#334155;")
        root.addWidget(self.label_status)

        self.btn_register.clicked.connect(self._on_register)
        self.btn_login.clicked.connect(self._on_login)
        self.btn_cancel.clicked.connect(self.reject)

    @staticmethod
    def _read_http_error(exc):
        return ApiClient.read_http_error(exc)

    def _set_status(self, text, error=False):
        color = "#b91c1c" if error else "#065f46"
        self.label_status.setStyleSheet(f"color:{color};")
        self.label_status.setText(text)

    def _collect_inputs(self):
        base = self.edit_api.text().strip().rstrip("/")
        if not base:
            base = "http://127.0.0.1:8000"
        username = self.edit_username.text().strip()
        password = self.edit_password.text()
        if not username or not password:
            raise RuntimeError("请输入用户名和密码")
        self.api_base_url = base
        self.api_client.set_base_url(base)
        return base, username, password

    def _request_json(self, method, path, payload):
        return self.api_client.request_json(method, path, payload=payload, timeout=20)

    def _on_register(self):
        try:
            _, username, password = self._collect_inputs()
            data = self._request_json("POST", "/register", {"username": username, "password": password})
            self._set_status(f"注册成功: {data.get('username', username)}")
            QMessageBox.information(self, "提示", "注册成功，请点击登录进入系统。", QMessageBox.Yes)
        except urllib.error.HTTPError as exc:
            self._set_status(f"注册失败: HTTP {exc.code}", error=True)
            QMessageBox.critical(self, "错误", f"注册失败 (HTTP {exc.code})\n{self._read_http_error(exc)}", QMessageBox.Yes)
        except urllib.error.URLError as exc:
            self._set_status("注册失败: 无法连接 API", error=True)
            QMessageBox.critical(self, "错误", f"无法连接 API:\n{exc.reason}", QMessageBox.Yes)
        except Exception as exc:
            self._set_status(f"注册失败: {exc}", error=True)
            QMessageBox.critical(self, "错误", f"注册失败:\n{exc}", QMessageBox.Yes)

    def _on_login(self):
        try:
            _, username, password = self._collect_inputs()
            data = self._request_json("POST", "/login", {"username": username, "password": password})
            self.username = username
            self.password = password
            self.user_id = data.get("id")
            self._set_status(f"登录成功: {username}")
            self.accept()
        except urllib.error.HTTPError as exc:
            self._set_status(f"登录失败: HTTP {exc.code}", error=True)
            QMessageBox.critical(self, "错误", f"登录失败 (HTTP {exc.code})\n{self._read_http_error(exc)}", QMessageBox.Yes)
        except urllib.error.URLError as exc:
            self._set_status("登录失败: 无法连接 API", error=True)
            QMessageBox.critical(self, "错误", f"无法连接 API:\n{exc.reason}", QMessageBox.Yes)
        except Exception as exc:
            self._set_status(f"登录失败: {exc}", error=True)
            QMessageBox.critical(self, "错误", f"登录失败:\n{exc}", QMessageBox.Yes)


class AccountDialog(QtWidgets.QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.setWindowTitle("账号中心")
        self.setMinimumSize(580, 500)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        form = QtWidgets.QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.edit_api_base = QtWidgets.QLineEdit(self.main.api_base_url)
        self.edit_api_base.setPlaceholderText("http://127.0.0.1:8000")
        form.addRow("API Base URL", self.edit_api_base)

        self.view_username = QtWidgets.QLineEdit()
        self.view_username.setReadOnly(True)
        self.btn_copy_username = QtWidgets.QPushButton("复制")
        username_row = QtWidgets.QWidget()
        username_layout = QtWidgets.QHBoxLayout(username_row)
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.setSpacing(8)
        username_layout.addWidget(self.view_username, 1)
        username_layout.addWidget(self.btn_copy_username)
        form.addRow("当前账号", username_row)

        self.view_password = QtWidgets.QLineEdit()
        self.view_password.setReadOnly(True)
        self.btn_copy_password = QtWidgets.QPushButton("复制")
        password_row = QtWidgets.QWidget()
        password_layout = QtWidgets.QHBoxLayout(password_row)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(8)
        password_layout.addWidget(self.view_password, 1)
        password_layout.addWidget(self.btn_copy_password)
        form.addRow("当前密码", password_row)

        root.addLayout(form)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        self.btn_refresh_jobs = QtWidgets.QPushButton("刷新我的任务")
        self.btn_close = QtWidgets.QPushButton("关闭")
        row.addWidget(self.btn_refresh_jobs)
        row.addWidget(self.btn_close)
        root.addLayout(row)

        self.label_status = QtWidgets.QLabel("")
        self.label_status.setStyleSheet("color: #1f2937;")
        root.addWidget(self.label_status)

        self.jobs_text = QtWidgets.QPlainTextEdit()
        self.jobs_text.setReadOnly(True)
        self.jobs_text.setPlaceholderText("显示当前登录用户最近任务")
        root.addWidget(self.jobs_text, 1)

        self.btn_copy_username.clicked.connect(lambda: self._copy_to_clipboard(self.view_username.text(), "username"))
        self.btn_copy_password.clicked.connect(lambda: self._copy_to_clipboard(self.view_password.text(), "password"))
        self.btn_refresh_jobs.clicked.connect(self._on_refresh_jobs)
        self.btn_close.clicked.connect(self.accept)

        self._update_view()

    def _sync_api_base_url(self):
        base_url = self.edit_api_base.text().strip()
        self.main.set_api_base_url(base_url)
        self.edit_api_base.setText(self.main.api_base_url)

    def _set_status(self, text, error=False):
        color = "#b91c1c" if error else "#065f46"
        self.label_status.setStyleSheet(f"color: {color};")
        self.label_status.setText(text)

    def _copy_to_clipboard(self, value, field_name):
        QApplication.clipboard().setText(value or "")
        if field_name == "username":
            self._set_status("账号已复制")
        elif field_name == "password":
            self._set_status("密码已复制")
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
        if not items:
            self.jobs_text.setPlainText("暂无任务记录")
            return
        lines = []
        for item in items:
            lines.append(
                f"{item.get('created_at', '-')}"
                f" | {item.get('job_id', '-')}"
                f" | {item.get('status', '-')}"
                f" | elapsed_ms={item.get('elapsed_ms')}"
            )
        self.jobs_text.setPlainText("\n".join(lines))

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
