"""Dialog for generating search queries."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QFrame
)
from PySide6.QtCore import Qt


class QueryGenerateDialog(QDialog):
    """Dialog for selecting query generation options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Search Queries")
        self.setMinimumWidth(400)
        self.selected_count = 5
        self.replace_existing = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("How many queries to generate?")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1e293b;")
        layout.addWidget(title)

        # Count selection
        count_frame = QFrame()
        count_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        count_layout = QHBoxLayout(count_frame)
        count_layout.setContentsMargins(16, 12, 16, 12)
        count_layout.setSpacing(16)

        self.count_group = QButtonGroup(self)
        counts = [5, 10, 20, 30]

        for i, count in enumerate(counts):
            radio = QRadioButton(str(count))
            radio.setStyleSheet("""
                QRadioButton {
                    font-size: 14px;
                    color: #374151;
                    spacing: 6px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
            """)
            if count == 5:
                radio.setChecked(True)
            self.count_group.addButton(radio, count)
            count_layout.addWidget(radio)

        count_layout.addStretch()
        layout.addWidget(count_frame)

        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)

        self.generate_btn = QPushButton("Generate 5 new queries")
        self.generate_btn.setMinimumHeight(44)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.generate_btn.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.generate_btn)

        self.replace_btn = QPushButton("Remove current queries and generate 5 new")
        self.replace_btn.setMinimumHeight(44)
        self.replace_btn.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                color: #991b1b;
                font-size: 14px;
                font-weight: 500;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #fecaca; }
        """)
        self.replace_btn.clicked.connect(self._on_replace)
        btn_layout.addWidget(self.replace_btn)

        layout.addLayout(btn_layout)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64748b;
                font-size: 14px;
                border: none;
                padding: 8px;
            }
            QPushButton:hover { color: #475569; }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

        # Connect radio buttons to update button text
        self.count_group.buttonClicked.connect(self._update_button_text)

    def _update_button_text(self):
        count = self.count_group.checkedId()
        self.generate_btn.setText(f"Generate {count} new queries")
        self.replace_btn.setText(f"Remove current queries and generate {count} new")

    def _on_generate(self):
        self.selected_count = self.count_group.checkedId()
        self.replace_existing = False
        self.accept()

    def _on_replace(self):
        self.selected_count = self.count_group.checkedId()
        self.replace_existing = True
        self.accept()
