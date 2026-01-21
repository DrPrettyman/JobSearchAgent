"""Dialog for selecting credentials."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QLineEdit, QDialogButtonBox, QPushButton, QButtonGroup
)
from PySide6.QtCore import Qt


# Common credential options
CREDENTIAL_OPTIONS = ["PhD", "MD", "JD", "MBA", "MS", "MA", "CPA", "PMP"]


class CredentialsDialog(QDialog):
    """Dialog for selecting a credential to add."""

    def __init__(self, existing_credentials: list[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Credential")
        self.setMinimumWidth(300)
        self._existing = set(existing_credentials or [])
        self._selected = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Instructions
        instructions = QLabel("Select a credential to add:")
        instructions.setStyleSheet("font-size: 14px; color: #374151;")
        layout.addWidget(instructions)

        # Radio buttons for common options
        self.button_group = QButtonGroup(self)

        for cred in CREDENTIAL_OPTIONS:
            radio = QRadioButton(cred)
            radio.setStyleSheet("font-size: 14px;")
            # Disable if already exists
            if cred in self._existing:
                radio.setEnabled(False)
                radio.setText(f"{cred} (already added)")
            self.button_group.addButton(radio)
            layout.addWidget(radio)

        # Other option with text entry
        other_row = QHBoxLayout()
        self.other_radio = QRadioButton("Other:")
        self.other_radio.setStyleSheet("font-size: 14px;")
        self.button_group.addButton(self.other_radio)
        other_row.addWidget(self.other_radio)

        self.other_entry = QLineEdit()
        self.other_entry.setPlaceholderText("Enter credential")
        self.other_entry.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2563eb;
            }
        """)
        self.other_entry.setEnabled(False)
        self.other_radio.toggled.connect(self.other_entry.setEnabled)
        other_row.addWidget(self.other_entry, 1)

        layout.addLayout(other_row)

        layout.addSpacing(8)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)

        add_btn = QPushButton("Add")
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
        """Handle add button click."""
        checked = self.button_group.checkedButton()
        if checked is None:
            return

        if checked == self.other_radio:
            text = self.other_entry.text().strip()
            if text and text not in self._existing:
                self._selected = text
                self.accept()
        else:
            self._selected = checked.text()
            self.accept()

    def get_credential(self) -> str | None:
        """Return the selected credential."""
        return self._selected
