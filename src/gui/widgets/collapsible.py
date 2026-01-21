"""Collapsible section widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon


class CollapsibleSection(QWidget):
    """A section that can be collapsed/expanded."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._is_expanded = True

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self.toggle_button = QPushButton(f"▼  {title}")
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: none;
                padding: 12px 16px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle)
        layout.addWidget(self.toggle_button)

        # Content container
        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-top: none;
                border-radius: 0 0 6px 6px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(self.content_area)

        self._title = title

    def set_content(self, widget: QWidget):
        """Set the content widget for the collapsible section."""
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.content_layout.addWidget(widget)

    def add_widget(self, widget: QWidget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)

    def toggle(self):
        """Toggle the expanded/collapsed state."""
        self._is_expanded = not self._is_expanded
        self.content_area.setVisible(self._is_expanded)

        # Update arrow
        arrow = "▼" if self._is_expanded else "▶"
        self.toggle_button.setText(f"{arrow}  {self._title}")

    def expand(self):
        """Expand the section."""
        if not self._is_expanded:
            self.toggle()

    def collapse(self):
        """Collapse the section."""
        if self._is_expanded:
            self.toggle()

    def is_expanded(self) -> bool:
        """Return whether the section is expanded."""
        return self._is_expanded
