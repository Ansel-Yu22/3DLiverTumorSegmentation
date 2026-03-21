import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from desktop.ui.login_dialog import LoginGateDialog
from desktop.ui.main_window import MainWindow


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)

    default_api = os.environ.get("SEG_API_BASE_URL", "http://127.0.0.1:8000")
    login_gate = LoginGateDialog(default_api)
    if login_gate.exec_() != QtWidgets.QDialog.Accepted:
        sys.exit(0)

    window = MainWindow(
        api_base_url=login_gate.api_base_url,
        auth_username=login_gate.username,
        auth_password=login_gate.password,
        auth_user_id=login_gate.user_id,
    )
    window.show()
    sys.exit(app.exec_())
