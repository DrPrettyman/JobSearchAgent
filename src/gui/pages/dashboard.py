"""Dashboard page - main overview with stats and quick actions."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from data_handlers import User


class StatCard(QFrame):
    """A card displaying a single statistic."""

    clicked = Signal(str)  # Emits the stat identifier

    def __init__(self, title: str, value: int, color: str, identifier: str = "", parent=None):
        super().__init__(parent)
        self.identifier = identifier
        self._setup_ui(title, value, color)

    def _setup_ui(self, title: str, value: int, color: str):
        self.setStyleSheet("background: transparent; border: none;")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(120, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"font-size: 42px; font-weight: bold; color: {color};")
        layout.addWidget(self.value_label)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 14px; color: #64748b;")
        layout.addWidget(self.title_label)

    def set_value(self, value: int):
        self.value_label.setText(str(value))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.identifier:
            self.clicked.emit(self.identifier)
        super().mousePressEvent(event)


class DashboardPage(QWidget):
    """Main dashboard with statistics and quick actions."""

    navigate_to = Signal(str)  # Emitted when user wants to navigate somewhere

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self._setup_ui()

    def _setup_ui(self):
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: #f8fafc;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Welcome header
        welcome_text = f"Welcome back, {self.user.name or self.user.username}"
        header = QLabel(welcome_text)
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e293b; background: transparent; border: none;")
        layout.addWidget(header)

        # Stats cards row (centered)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        stats_layout.addStretch()

        self.pending_card = StatCard("Pending", 0, "#ca8a04", "jobs_pending")
        self.pending_card.clicked.connect(self.navigate_to)
        stats_layout.addWidget(self.pending_card)

        self.in_progress_card = StatCard("In Progress", 0, "#0891b2", "jobs_in_progress")
        self.in_progress_card.clicked.connect(self.navigate_to)
        stats_layout.addWidget(self.in_progress_card)

        self.applied_card = StatCard("Applied", 0, "#16a34a", "jobs_applied")
        self.applied_card.clicked.connect(self.navigate_to)
        stats_layout.addWidget(self.applied_card)

        self.discarded_card = StatCard("Discarded", 0, "#dc2626", "jobs_discarded")
        self.discarded_card.clicked.connect(self.navigate_to)
        stats_layout.addWidget(self.discarded_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Profile summary section
        profile_card = QFrame()
        profile_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        profile_layout = QVBoxLayout(profile_card)
        profile_layout.setContentsMargins(20, 20, 20, 20)
        profile_layout.setSpacing(6)

        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1e293b; background: transparent; border: none; padding: 0; margin: 0;")
        profile_layout.addWidget(self.name_label)

        self.email_label = QLabel()
        self.email_label.setStyleSheet("font-size: 14px; color: #64748b; background: transparent; border: none; padding: 0; margin: 0;")
        profile_layout.addWidget(self.email_label)

        # Add some spacing before job preferences
        profile_layout.addSpacing(8)

        self.titles_label = QLabel()
        self.titles_label.setStyleSheet("font-size: 14px; color: #64748b; background: transparent; border: none; padding: 0; margin: 0;")
        self.titles_label.setWordWrap(True)
        profile_layout.addWidget(self.titles_label)

        self.locations_label = QLabel()
        self.locations_label.setStyleSheet("font-size: 14px; color: #64748b; background: transparent; border: none; padding: 0; margin: 0;")
        self.locations_label.setWordWrap(True)
        profile_layout.addWidget(self.locations_label)

        layout.addWidget(profile_card)

        layout.addStretch()

        scroll.setWidget(content)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def refresh(self):
        """Refresh dashboard data."""
        job_handler = self.user.job_handler

        # Update stats
        self.pending_card.set_value(job_handler.number_pending)
        self.in_progress_card.set_value(job_handler.number_in_progress)
        self.applied_card.set_value(job_handler.number_applied)
        self.discarded_card.set_value(job_handler.number_discarded)

        # Update profile summary
        name = self.user.name_with_credentials if self.user.name else "Not set"
        self.name_label.setText(name)
        self.email_label.setText(self.user.email or "No email set")

        titles = self.user.desired_job_titles
        if titles:
            self.titles_label.setText(f"Looking for: {', '.join(titles)}")
        else:
            self.titles_label.setText("No job titles configured")

        locations = self.user.desired_job_locations
        if locations:
            self.locations_label.setText(f"Locations: {', '.join(locations)}")
        else:
            self.locations_label.setText("No locations configured")
            