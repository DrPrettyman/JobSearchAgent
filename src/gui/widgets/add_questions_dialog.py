"""Dialog for adding multiple application questions."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QPushButton
)
from PySide6.QtCore import Qt


class AddQuestionsDialog(QDialog):
    """Dialog for pasting multiple questions, one per line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Application Questions")
        self.setMinimumSize(500, 400)
        self._questions = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Instructions
        instructions = QLabel("Paste your application questions below (one per line):")
        instructions.setStyleSheet("font-size: 14px; color: #374151;")
        layout.addWidget(instructions)

        # Text edit area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Why do you want to work at this company?\n"
            "Describe your experience with...\n"
            "What are your salary expectations?"
        )
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
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)

        add_btn = QPushButton("Add Questions")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self._on_add)
        buttons.addButton(add_btn, QDialogButtonBox.AcceptRole)

        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_add(self):
        """Parse questions and accept dialog."""
        text = self.text_edit.toPlainText()
        lines = text.strip().split('\n')
        self._questions = [line.strip() for line in lines if line.strip()]
        if self._questions:
            self.accept()

    def get_questions(self) -> list[str]:
        """Return the list of parsed questions."""
        return self._questions
