"""Text edit dialog for viewing/editing long text content."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QPushButton
)
from PySide6.QtCore import Qt


class TextEditDialog(QDialog):
    """Dialog with a large text area for viewing or editing text."""

    def __init__(self, title: str, text: str, readonly: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
        self._readonly = readonly
        self._setup_ui(text)

    def _setup_ui(self, text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Text edit area
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(self._readonly)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.5;
                background: white;
            }
            QTextEdit:focus {
                border-color: #2563eb;
            }
        """)
        layout.addWidget(self.text_edit)

        # Buttons
        if self._readonly:
            buttons = QDialogButtonBox(QDialogButtonBox.Close)
            buttons.rejected.connect(self.reject)
        else:
            buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)

            # Style the save button
            save_btn = buttons.button(QDialogButtonBox.Save)
            save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                }
                QPushButton:hover { background-color: #1d4ed8; }
            """)

        layout.addWidget(buttons)

    def get_text(self) -> str:
        """Return the current text content."""
        return self.text_edit.toPlainText()
