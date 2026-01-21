"""Status badge widget for displaying job status."""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from data_handlers import JobStatus


STATUS_STYLES = {
    JobStatus.TEMP: {
        "text": "Temp",
        "icon": "◌",
        "bg": "#f1f5f9",
        "fg": "#64748b",
    },
    JobStatus.PENDING: {
        "text": "Pending",
        "icon": "○",
        "bg": "#fef3c7",
        "fg": "#92400e",
    },
    JobStatus.IN_PROGRESS: {
        "text": "In Progress",
        "icon": "▶",
        "bg": "#cffafe",
        "fg": "#155e75",
    },
    JobStatus.APPLIED: {
        "text": "Applied",
        "icon": "✓",
        "bg": "#dcfce7",
        "fg": "#166534",
    },
    JobStatus.DISCARDED: {
        "text": "Discarded",
        "icon": "✗",
        "bg": "#fee2e2",
        "fg": "#991b1b",
    },
}


class StatusBadge(QLabel):
    """A colored badge showing job status."""

    def __init__(self, status: JobStatus = None, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        if status:
            self.set_status(status)

    def set_status(self, status: JobStatus):
        """Update the badge to show a new status."""
        style = STATUS_STYLES.get(status, STATUS_STYLES[JobStatus.PENDING])

        self.setText(f"{style['icon']} {style['text']}")
        self.setStyleSheet(f"""
            background-color: {style['bg']};
            color: {style['fg']};
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 500;
            font-size: 12px;
        """)
