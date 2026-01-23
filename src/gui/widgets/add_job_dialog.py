"""Dialog for adding a job manually or from URL."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QWidget
)
from PySide6.QtCore import Qt


class AddJobDialog(QDialog):
    """Dialog for adding a new job."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Job")
        self.setMinimumWidth(450)
        self._result = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Mode selection
        mode_label = QLabel("How would you like to add the job?")
        mode_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")
        layout.addWidget(mode_label)

        self.mode_group = QButtonGroup(self)

        self.url_radio = QRadioButton("Paste a job posting URL (auto-scrape)")
        self.url_radio.setStyleSheet("font-size: 13px; color: #374151;")
        self.url_radio.setChecked(True)
        self.mode_group.addButton(self.url_radio)
        layout.addWidget(self.url_radio)

        self.manual_radio = QRadioButton("Enter details manually")
        self.manual_radio.setStyleSheet("font-size: 13px; color: #374151;")
        self.mode_group.addButton(self.manual_radio)
        layout.addWidget(self.manual_radio)

        # URL input section
        self.url_section = QWidget()
        url_layout = QVBoxLayout(self.url_section)
        url_layout.setContentsMargins(0, 8, 0, 0)
        url_layout.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        self.url_input.setStyleSheet(self._input_style())
        url_layout.addWidget(self._make_field("Job URL", self.url_input))

        layout.addWidget(self.url_section)

        # Manual input section
        self.manual_section = QWidget()
        manual_layout = QVBoxLayout(self.manual_section)
        manual_layout.setContentsMargins(0, 8, 0, 0)
        manual_layout.setSpacing(8)

        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("Company name")
        self.company_input.setStyleSheet(self._input_style())
        manual_layout.addWidget(self._make_field("Company *", self.company_input))

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Job title")
        self.title_input.setStyleSheet(self._input_style())
        manual_layout.addWidget(self._make_field("Title *", self.title_input))

        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("https://... (optional)")
        self.link_input.setStyleSheet(self._input_style())
        manual_layout.addWidget(self._make_field("Link", self.link_input))

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("City, State (optional)")
        self.location_input.setStyleSheet(self._input_style())
        manual_layout.addWidget(self._make_field("Location", self.location_input))

        layout.addWidget(self.manual_section)
        self.manual_section.hide()

        # Connect mode toggle
        self.url_radio.toggled.connect(self._on_mode_changed)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #e2e8f0; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.add_btn = QPushButton("Add Job")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #94a3b8; }
        """)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

    def _input_style(self) -> str:
        return """
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus { border-color: #2563eb; }
        """

    def _make_field(self, label: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(lbl)
        layout.addWidget(widget)

        return container

    def _on_mode_changed(self, url_checked: bool):
        self.url_section.setVisible(url_checked)
        self.manual_section.setVisible(not url_checked)

    def _on_add(self):
        if self.url_radio.isChecked():
            url = self.url_input.text().strip()
            if url:
                self._result = {"mode": "url", "url": url}
                self.accept()
        else:
            company = self.company_input.text().strip()
            title = self.title_input.text().strip()
            if company and title:
                self._result = {
                    "mode": "manual",
                    "company": company,
                    "title": title,
                    "link": self.link_input.text().strip(),
                    "location": self.location_input.text().strip(),
                }
                self.accept()

    def get_result(self) -> dict | None:
        return self._result
