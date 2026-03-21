BUTTON_STYLE = """
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

ACTION_PRIMARY_STYLE = """
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

ACTION_SECONDARY_STYLE = """
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

LINE_EDIT_STYLE = (
    "border: 1px solid #c8d3df; background-color: #fff; border-radius: 10px;"
    " padding: 6px 10px; color:#334155;"
)
LABEL_STYLE = "border: 1px solid #c8d3df; background-color: #fff; border-radius: 10px;"

PROGRESS_STYLE = """
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
"""

GROUP_BOX_STYLE = "QGroupBox { background:#fff; border:1px solid #c8d3df; border-radius: 10px; margin-top:0px; }"

STATUS_BAR_STYLE = "QStatusBar { border-top: 1px solid #c8d3df; background: #f8fafc; color: #334155; }"

LOGIN_EDIT_STYLE = (
    "QLineEdit {border:1px solid #cbd5e1; border-radius:6px; padding:6px 8px; background:white;}"
    "QLineEdit:focus {border:1px solid #2563eb;}"
)
LOGIN_BUTTON_STYLE = (
    "QPushButton {background:#2563eb; color:white; border:none; border-radius:6px; padding:6px 10px;}"
    "QPushButton:hover {background:#1d4ed8;}"
    "QPushButton:disabled {background:#93c5fd;}"
)

READONLY_STYLE = (
    "QLineEdit {border:1px solid #cbd5e1; border-radius:6px; padding:6px 8px; background:#f8fafc; color:#0f172a;}"
)
PRIMARY_BUTTON_STYLE = (
    "QPushButton {background:#2563eb; color:white; border:none; border-radius:6px; padding:6px 12px;}"
    "QPushButton:hover {background:#1d4ed8;}"
    "QPushButton:disabled {background:#93c5fd; color:#e2e8f0;}"
)
SECONDARY_BUTTON_STYLE = (
    "QPushButton {background:#e2e8f0; color:#0f172a; border:1px solid #cbd5e1; border-radius:6px; padding:6px 10px;}"
    "QPushButton:hover {background:#dbe5f1;}"
    "QPushButton:disabled {background:#f1f5f9; color:#94a3b8; border-color:#e2e8f0;}"
)
ROW_LABEL_STYLE = "color:#0f172a; padding-right:2px;"

JOBS_TABLE_STYLE = (
    "QTableWidget {border:1px solid #cbd5e1; border-radius:6px; background:white; gridline-color:#e2e8f0;}"
    "QHeaderView::section {background:#f8fafc; border:0px; border-bottom:1px solid #e2e8f0; padding:6px; color:#334155;}"
    "QTableWidget::item {padding:4px;}"
    "QTableWidget::item:selected {background:#dbeafe; color:#0f172a;}"
)

