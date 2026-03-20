import urllib.error
from datetime import datetime, timezone

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from Desktop.api_client import ApiClient
from Desktop.view_ui import AccountDialogUiMixin, LoginGateDialogUiMixin


class LoginGateDialog(QtWidgets.QDialog, LoginGateDialogUiMixin):
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


class AccountDialog(QtWidgets.QDialog, AccountDialogUiMixin):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.setup_account_ui(self.main.api_base_url)

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
