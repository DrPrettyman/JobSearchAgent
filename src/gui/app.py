"""Application setup and theming."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt

from data_handlers import User
from gui.main_window import MainWindow


# Color scheme
COLORS = {
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "success": "#16a34a",
    "warning": "#ca8a04",
    "error": "#dc2626",
    "pending": "#ca8a04",
    "in_progress": "#0891b2",
    "applied": "#16a34a",
    "discarded": "#dc2626",
}


def get_stylesheet() -> str:
    """Return the application stylesheet."""
    return """
        /* Global */
        QMainWindow {
            background-color: #f8fafc;
        }

        QWidget {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
        }

        /* Top Navbar */
        #navbar {
            background-color: #1e293b;
        }

        #navbar QPushButton {
            background-color: transparent;
            color: #94a3b8;
            border: none;
            padding: 16px 20px;
            font-size: 14px;
            border-radius: 0;
        }

        #navbar QPushButton:hover {
            background-color: #334155;
            color: #f1f5f9;
        }

        #navbar QPushButton:checked {
            color: white;
            border-bottom: 3px solid #2563eb;
        }

        #navbar_header {
            color: #f1f5f9;
            font-size: 18px;
            font-weight: bold;
        }

        #navbar_user {
            color: #94a3b8;
            padding: 0 8px;
        }

        /* Content area */
        #content_area {
            background-color: #f8fafc;
        }

        /* Page headers */
        .page-header {
            font-size: 24px;
            font-weight: bold;
            color: #1e293b;
            padding: 20px 0;
        }

        /* Cards */
        .card {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
        }

        .card:hover {
            border-color: #cbd5e1;
        }

        /* Stat cards */
        .stat-card {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            min-width: 150px;
        }

        .stat-value {
            font-size: 32px;
            font-weight: bold;
        }

        .stat-label {
            font-size: 14px;
            color: #64748b;
        }

        /* Buttons */
        QPushButton {
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 500;
        }

        QPushButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton:pressed {
            background-color: #1e40af;
        }

        QPushButton:disabled {
            background-color: #94a3b8;
        }

        QPushButton.secondary {
            background-color: #f1f5f9;
            color: #475569;
            border: 1px solid #e2e8f0;
        }

        QPushButton.secondary:hover {
            background-color: #e2e8f0;
        }

        QPushButton.success {
            background-color: #16a34a;
        }

        QPushButton.success:hover {
            background-color: #15803d;
        }

        QPushButton.warning {
            background-color: #ca8a04;
        }

        QPushButton.warning:hover {
            background-color: #a16207;
        }

        QPushButton.danger {
            background-color: #dc2626;
        }

        QPushButton.danger:hover {
            background-color: #b91c1c;
        }

        /* Input fields */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 8px 12px;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #2563eb;
            outline: none;
        }

        /* Lists */
        QListWidget {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 4px;
        }

        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
        }

        QListWidget::item:hover {
            background-color: #f1f5f9;
        }

        QListWidget::item:selected {
            background-color: #dbeafe;
            color: #1e40af;
        }

        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background-color: white;
        }

        QTabBar::tab {
            background-color: #f1f5f9;
            color: #475569;
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }

        QTabBar::tab:selected {
            background-color: white;
            color: #1e293b;
        }

        QTabBar::tab:hover:!selected {
            background-color: #e2e8f0;
        }

        /* Scroll bars */
        QScrollBar:vertical {
            background-color: #f1f5f9;
            width: 10px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background-color: #cbd5e1;
            border-radius: 5px;
            min-height: 30px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #94a3b8;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }

        /* Labels */
        QLabel.section-header {
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
            padding: 8px 0;
        }

        QLabel.field-label {
            font-size: 14px;
            color: #64748b;
        }

        QLabel.field-value {
            font-size: 14px;
            color: #1e293b;
        }

        /* Status badges */
        .status-pending {
            background-color: #fef3c7;
            color: #92400e;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 500;
        }

        .status-in-progress {
            background-color: #cffafe;
            color: #155e75;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 500;
        }

        .status-applied {
            background-color: #dcfce7;
            color: #166534;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 500;
        }

        .status-discarded {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 500;
        }

        /* Progress bar */
        QProgressBar {
            background-color: #e2e8f0;
            border: none;
            border-radius: 4px;
            height: 8px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #2563eb;
            border-radius: 4px;
        }

        /* Tooltips */
        QToolTip {
            background-color: #1e293b;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
        }

        /* Message box */
        QMessageBox {
            background-color: white;
        }

        /* Combo box */
        QComboBox {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 8px 12px;
            min-width: 150px;
        }

        QComboBox:hover {
            border-color: #cbd5e1;
        }

        QComboBox::drop-down {
            border: none;
            padding-right: 8px;
        }

        QComboBox QAbstractItemView {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            selection-background-color: #dbeafe;
        }
    """


def run_gui(username: str):
    """Run the GUI application."""
    app = QApplication(sys.argv)

    # Apply stylesheet
    app.setStyleSheet(get_stylesheet())

    # Load user
    user = User(username=username)

    # Create and show main window
    window = MainWindow(user)
    window.show()

    sys.exit(app.exec())
