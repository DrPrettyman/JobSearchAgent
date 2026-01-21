"""Tag widgets with flow layout for wrapping."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal

from gui.styles import make_label


class Tag(QFrame):
    """A tag/chip with text and remove button."""

    removed = Signal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(28)
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: #e0e7ff; border: none; border-radius: 14px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 8, 5)
        layout.setSpacing(4)

        label = QLabel(text)
        label.setStyleSheet("font-size: 13px; color: #3730a3; background: transparent; border: none; padding: 0; margin: 0;")
        layout.addWidget(label)

        remove_btn = QPushButton("x")
        remove_btn.setFixedSize(18, 18)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6366f1;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 0;
                margin: 0;
            }
            QPushButton:hover {
                color: #4338ca;
            }
        """)
        remove_btn.clicked.connect(lambda: self.removed.emit(self.text))
        layout.addWidget(remove_btn)


class FlowWidget(QWidget):
    """A widget that lays out children in a flowing/wrapping manner."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._h_spacing = 6
        self._v_spacing = 6

    def addWidget(self, widget):
        widget.setParent(self)
        self._items.append(widget)
        self._do_layout()

    def clear(self):
        for widget in self._items:
            widget.deleteLater()
        self._items = []

    def _do_layout(self):
        if not self._items:
            self.setMinimumHeight(0)
            return

        width = self.width() if self.width() > 0 else 400
        x = 0
        y = 0
        row_height = 0

        for widget in self._items:
            widget.adjustSize()
            item_width = widget.sizeHint().width()
            item_height = widget.sizeHint().height()

            if x + item_width > width and x > 0:
                # Wrap to next row
                x = 0
                y += row_height + self._v_spacing
                row_height = 0

            widget.move(x, y)
            widget.show()
            x += item_width + self._h_spacing
            row_height = max(row_height, item_height)

        self.setMinimumHeight(y + row_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._do_layout()


class TagContainer(QWidget):
    """Container for tags with flow layout."""

    tag_removed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        self._empty_label = make_label("None added yet")
        self._layout.addWidget(self._empty_label)

        self._flow = FlowWidget()
        self._flow.setStyleSheet("background: transparent;")
        self._layout.addWidget(self._flow)
        self._flow.hide()

    def set_tags(self, items: list[str]):
        """Set the tags to display."""
        self._flow.clear()

        if not items:
            self._empty_label.show()
            self._flow.hide()
            return

        self._empty_label.hide()
        self._flow.show()

        for text in items:
            tag = Tag(text)
            tag.removed.connect(self.tag_removed.emit)
            self._flow.addWidget(tag)
