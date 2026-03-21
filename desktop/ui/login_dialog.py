import urllib.error

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from desktop.infra.api_client import ApiClient
from desktop.ui.login_dialog_ui import LoginDialogUiMixin


class LoginGateDialog(QtWidgets.QDialog, LoginDialogUiMixin):
    def __init__(self, default_api_base):
        super().__init__()
        self.api_base_url = (default_api_base or "http://127.0.0.1:8000").rstrip("/")
        self.api_client = ApiClient(self.api_base_url)
        self.username = None
        self.password = None
        self.user_id = None
        self.settings = QSettings("LiverSeg", "LoginGate")

        saved_api = self.settings.value("api_base_url", self.api_base_url, type=str)
        self.setup_login_ui(saved_api)

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

    def _persist_inputs(self, base):
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
            self._persist_inputs(base)
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
            self._persist_inputs(base)
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
