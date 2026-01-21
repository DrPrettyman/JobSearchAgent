"""Job card widget for displaying job summary in lists."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from data_handlers import Job
from gui.widgets.status_badge import StatusBadge


class JobCard(QFrame):
    """A card widget displaying job summary information."""

    clicked = Signal(str)  # Emits job_id when clicked

    def __init__(self, job: Job = None, parent=None):
        super().__init__(parent)
        self.job = job
        self.job_id = job.id if job is not None else None

        self._setup_ui()
        if job is not None:
            self.set_job(job)

    def _setup_ui(self):
        """Set up the card UI."""
        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            JobCard {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            JobCard:hover {
                border-color: #2563eb;
                background-color: #f8fafc;
            }
            JobCard QLabel {
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Top row: Company and status
        top_row = QHBoxLayout()

        self.company_label = QLabel()
        self.company_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #1e293b;")
        self.company_label.setWordWrap(True)
        top_row.addWidget(self.company_label, 1)

        top_row.addStretch()

        self.status_badge = StatusBadge()
        top_row.addWidget(self.status_badge)

        layout.addLayout(top_row)

        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #2563eb;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Bottom row: Location and date
        bottom_row = QHBoxLayout()

        self.location_label = QLabel()
        self.location_label.setStyleSheet("font-size: 13px; color: #64748b;")
        self.location_label.setWordWrap(True)
        bottom_row.addWidget(self.location_label, 1)

        bottom_row.addStretch()

        self.date_label = QLabel()
        self.date_label.setStyleSheet("font-size: 12px; color: #94a3b8;")
        bottom_row.addWidget(self.date_label)

        layout.addLayout(bottom_row)

    def set_job(self, job: Job):
        """Update the card with job data."""
        self.job = job
        self.job_id = job.id

        self.company_label.setText(job.company)
        self.title_label.setText(job.title)
        self.location_label.setText(job.location or "Location not specified")
        self.date_label.setText(job.date_found[:10] if job.date_found else "")
        self.status_badge.set_status(job.status)

    def mousePressEvent(self, event):
        """Handle click events."""
        if event.button() == Qt.LeftButton and self.job_id:
            self.clicked.emit(self.job_id)
        super().mousePressEvent(event)
