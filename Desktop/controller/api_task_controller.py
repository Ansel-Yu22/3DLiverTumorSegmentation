import os
import time
import urllib.error

import nibabel as nib
from PyQt5.QtWidgets import QMessageBox

from Desktop.infra.api_client import ApiClient
from Desktop.infra.path_utils import resolve_result_path


class ApiTaskControllerMixin:
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
                self,
                "错误",
                f"查询失败 (HTTP {exc.code})\n{self._read_http_error(exc)}",
                QMessageBox.Yes,
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
            self.ct_name = os.path.basename(ct_path).split("-")[-1]
            self.segmentation_data = nib.load(self.segmentation_path).get_fdata()
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
        if getattr(self, "local_seg_in_progress", False):
            QMessageBox.information(self, "提示", "本地分割任务正在运行，请稍候。", QMessageBox.Yes)
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
                self,
                "错误",
                f"提交失败 (HTTP {exc.code})\n{self._read_http_error(exc)}",
                QMessageBox.Yes,
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
