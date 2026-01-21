"""Removable list item and container widgets."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QCheckBox
from PySide6.QtCore import Qt, Signal

from gui.styles import make_label


class RemovableItem(QWidget):
    """A list item with text and remove button.

    Emits item_id on removal. If no item_id is provided, uses text as the id.
    Optionally shows a checkbox for selection.
    """

    removed = Signal(str)  # Emits item_id
    selection_changed = Signal(str, bool)  # Emits (item_id, is_checked)

    def __init__(self, text: str, item_id: str = None, tooltip: str = None, checkable: bool = False, parent=None):
        super().__init__(parent)
        self.item_id = item_id if item_id is not None else text
        self._checkable = checkable
        self._checkbox = None
        self._setup_ui(text, tooltip)

    def _setup_ui(self, text: str, tooltip: str = None):
        self.setStyleSheet("background: transparent;")
        if tooltip:
            self.setToolTip(tooltip)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Optional checkbox
        if self._checkable:
            self._checkbox = QCheckBox()
            self._checkbox.setStyleSheet("QCheckBox { background: transparent; }")
            self._checkbox.stateChanged.connect(self._on_checkbox_changed)
            layout.addWidget(self._checkbox)

        self._label = QLabel(text)
        self._label.setStyleSheet("font-size: 13px; color: #1e293b; background: transparent; border: none; padding: 0; margin: 0;")
        self._label.setWordWrap(True)
        layout.addWidget(self._label, 1)

        self._remove_btn = QPushButton("x")
        self._remove_btn.setFixedSize(20, 20)
        self._remove_btn.setCursor(Qt.PointingHandCursor)
        self._remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 0;
                margin: 0;
            }
            QPushButton:hover {
                color: #dc2626;
            }
        """)
        self._remove_btn.clicked.connect(lambda: self.removed.emit(self.item_id))
        self._remove_btn.enterEvent = self._on_btn_enter
        self._remove_btn.leaveEvent = self._on_btn_leave
        layout.addWidget(self._remove_btn)

    def _on_btn_enter(self, event):
        self._label.setStyleSheet("font-size: 13px; color: #dc2626; background: transparent; border: none; padding: 0; margin: 0;")

    def _on_btn_leave(self, event):
        self._label.setStyleSheet("font-size: 13px; color: #1e293b; background: transparent; border: none; padding: 0; margin: 0;")

    def _on_checkbox_changed(self, state):
        self.selection_changed.emit(self.item_id, state == Qt.Checked)

    def is_checked(self) -> bool:
        """Return whether the checkbox is checked."""
        return self._checkbox.isChecked() if self._checkbox else False

    def set_checked(self, checked: bool):
        """Set the checkbox state."""
        if self._checkbox:
            self._checkbox.setChecked(checked)


class RemovableList(QWidget):
    """Container for removable list items."""

    item_removed = Signal(str)  # Emits item_id
    selection_changed = Signal()  # Emits when any checkbox changes

    def __init__(self, empty_text: str = "None added yet", checkable: bool = False, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._checkable = checkable
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._items = []

        self._empty_label = make_label(empty_text)
        self._layout.addWidget(self._empty_label)

    def set_items(self, items: list[str]):
        """Set simple text items. Each item's text is used as its id."""
        self._clear_items()

        if not items:
            self._empty_label.show()
            return

        self._empty_label.hide()

        for text in items:
            item = RemovableItem(text, checkable=self._checkable)
            item.removed.connect(self.item_removed.emit)
            item.selection_changed.connect(lambda *_: self.selection_changed.emit())
            self._items.append(item)
            self._layout.addWidget(item)

    def set_items_with_ids(self, items: list):
        """Set items with custom ids.

        Args:
            items: List of objects with .id and display text attributes,
                   or list of (id, text, tooltip) tuples.
        """
        self._clear_items()

        if not items:
            self._empty_label.show()
            return

        self._empty_label.hide()

        for item_data in items:
            if isinstance(item_data, tuple):
                item_id, text, tooltip = item_data
            else:
                # Assume it's an object with .id and a text attribute
                item_id = item_data.id
                # Try common text attribute names
                text = getattr(item_data, 'query', None) or getattr(item_data, 'text', None) or str(item_data)
                # Truncate display text
                tooltip = text if len(text) > 80 else None
                if len(text) > 80:
                    text = text[:80] + "..."

            item = RemovableItem(text, item_id=item_id, tooltip=tooltip, checkable=self._checkable)
            item.removed.connect(self.item_removed.emit)
            item.selection_changed.connect(lambda *_: self.selection_changed.emit())
            self._items.append(item)
            self._layout.addWidget(item)

    def _clear_items(self):
        """Clear all items from the list."""
        for item in self._items:
            item.deleteLater()
        self._items = []

    def get_selected_ids(self) -> list[str]:
        """Return a list of item_ids for all checked items."""
        return [item.item_id for item in self._items if item.is_checked()]

    def select_all(self):
        """Check all checkboxes."""
        for item in self._items:
            item.set_checked(True)

    def deselect_all(self):
        """Uncheck all checkboxes."""
        for item in self._items:
            item.set_checked(False)

    def has_selection(self) -> bool:
        """Return True if any item is selected."""
        return any(item.is_checked() for item in self._items)
