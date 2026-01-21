"""Shared style helper functions for GUI components."""

from PySide6.QtWidgets import QFrame, QLabel, QPushButton


def make_card() -> QFrame:
    """Create a standard card container."""
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
        }
    """)
    return card


def make_section_title(text: str) -> QLabel:
    """Create a section title label."""
    label = QLabel(text)
    label.setStyleSheet("""
        font-size: 16px;
        font-weight: 600;
        color: #1e293b;
        background: transparent;
        border: none;
        padding: 0;
        margin: 0;
    """)
    return label


def make_label(text: str = "", muted: bool = True) -> QLabel:
    """Create a plain text label."""
    label = QLabel(text)
    color = "#64748b" if muted else "#1e293b"
    label.setStyleSheet(f"""
        font-size: 14px;
        color: {color};
        background: transparent;
        border: none;
        padding: 0;
        margin: 0;
    """)
    label.setWordWrap(True)
    return label


def make_primary_button(text: str) -> QPushButton:
    """Create a primary (blue) button."""
    btn = QPushButton(text)
    btn.setStyleSheet("""
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
    return btn


def make_secondary_button(text: str) -> QPushButton:
    """Create a secondary (gray) button."""
    btn = QPushButton(text)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #f1f5f9;
            color: #475569;
            border: 1px solid #e2e8f0;
            padding: 8px 16px;
            border-radius: 6px;
        }
        QPushButton:hover { background-color: #e2e8f0; }
    """)
    return btn


def make_danger_button(text: str) -> QPushButton:
    """Create a danger (red) button."""
    btn = QPushButton(text)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #fee2e2;
            color: #991b1b;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
        }
        QPushButton:hover { background-color: #fecaca; }
    """)
    return btn
