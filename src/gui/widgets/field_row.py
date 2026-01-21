"""Inline editable field row widget."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Signal


class FieldRow(QWidget):
    """A row with label and inline-editable value."""

    value_changed = Signal(str)

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.label_text = label
        self._current_value = ""
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Label
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-size: 14px; color: #64748b; background: transparent; border: none; padding: 0; margin: 0; min-width: 80px;")
        layout.addWidget(label_widget)

        # Editable value field
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Click to edit...")
        self.value_edit.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                color: #1e293b;
                background: transparent;
                border: none;
                border-bottom: 1px solid transparent;
                padding: 2px 0;
                margin: 0;
            }
            QLineEdit:hover {
                border-bottom: 1px solid #e2e8f0;
            }
            QLineEdit:focus {
                border-bottom: 1px solid #2563eb;
                background: #f8fafc;
            }
        """)
        self.value_edit.editingFinished.connect(self._on_editing_finished)
        layout.addWidget(self.value_edit, 1)

    def _on_editing_finished(self):
        new_value = self.value_edit.text().strip()
        if new_value != self._current_value:
            self._current_value = new_value
            self.value_changed.emit(new_value)

    def set_value(self, value: str):
        self._current_value = value or ""
        self.value_edit.setText(self._current_value)
