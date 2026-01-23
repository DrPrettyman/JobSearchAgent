"""Jobs list page - browse and filter jobs."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QButtonGroup, QSizePolicy, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from data_handlers import User, Job, JobStatus
from gui.widgets.job_card import JobCard
from gui.widgets.add_job_dialog import AddJobDialog
from gui.workers import Worker
from gui.styles import make_card


class FilterButton(QPushButton):
    """A filter toggle button."""

    def __init__(self, text: str, count: int = 0, color: str = "#64748b", parent=None):
        super().__init__(parent)
        self.base_text = text
        self.color = color
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.set_count(count)
        # Update style when toggled (works with QButtonGroup)
        self.toggled.connect(self._update_style)
        self._update_style()

    def set_count(self, count: int):
        self.count = count
        self.setText(f"{self.base_text} ({count})")

    def _update_style(self):
        # Always show the color - checked state is solid, unchecked is lighter
        if self.isChecked():
            bg = self.color
            hover_bg = self._darken(self.color)
        else:
            bg = self._lighten(self.color)
            hover_bg = self.color

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 14px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """)

    def _lighten(self, hex_color: str) -> str:
        """Return a lighter version of the color."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        # Blend 60% with white
        r = int(r * 0.4 + 255 * 0.6)
        g = int(g * 0.4 + 255 * 0.6)
        b = int(b * 0.4 + 255 * 0.6)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _darken(self, hex_color: str) -> str:
        """Return a darker version of the color."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = int(r * 0.8)
        g = int(g * 0.8)
        b = int(b * 0.8)
        return f"#{r:02x}{g:02x}{b:02x}"


class JobsListPage(QWidget):
    """Page for browsing and filtering jobs."""

    job_selected = Signal(str)  # Emits job_id when a job is clicked

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.current_filter = "pending"
        self.current_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("Jobs")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e293b;")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search jobs...")
        self.search_box.setFixedWidth(200)
        self.search_box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #2563eb;
            }
        """)
        self.search_box.textChanged.connect(self._on_search_changed)
        header_layout.addWidget(self.search_box)

        # Add job button
        add_btn = QPushButton("+ Add job manually")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        add_btn.clicked.connect(self._on_add_job)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Filter buttons in a card container
        filter_card = make_card()
        filter_card_layout = QHBoxLayout(filter_card)
        filter_card_layout.setContentsMargins(12, 12, 12, 12)
        filter_card_layout.setSpacing(8)

        self.filter_buttons = {}
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        filters = [
            ("pending", "Pending", "#ca8a04"),
            ("in_progress", "In Progress", "#0891b2"),
            ("applied", "Applied", "#16a34a"),
            ("discarded", "Discarded", "#dc2626"),
            ("all", "All", "#64748b"),
        ]

        for filter_id, label, color in filters:
            btn = FilterButton(label, 0, color)
            btn.clicked.connect(lambda checked, f=filter_id: self._on_filter_changed(f))
            filter_card_layout.addWidget(btn)
            self.filter_buttons[filter_id] = btn
            self.filter_group.addButton(btn)

        # Set "pending" as default
        self.filter_buttons["pending"].setChecked(True)

        filter_card_layout.addStretch()
        layout.addWidget(filter_card)

        # Jobs list (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: transparent;")

        self.jobs_container = QWidget()
        self.jobs_layout = QVBoxLayout(self.jobs_container)
        self.jobs_layout.setContentsMargins(0, 0, 0, 0)
        self.jobs_layout.setSpacing(12)
        self.jobs_layout.addStretch()

        scroll.setWidget(self.jobs_container)
        layout.addWidget(scroll)

        # Empty state label
        self.empty_label = QLabel("No jobs found")
        self.empty_label.setStyleSheet("font-size: 16px; color: #94a3b8; padding: 40px;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.hide()

    def _on_filter_changed(self, filter_id: str):
        self.current_filter = filter_id
        self.filter_buttons[filter_id].setChecked(True)
        self._refresh_jobs()

    def set_filter(self, filter_name: str):
        """Set the current filter programmatically."""
        if filter_name in self.filter_buttons:
            self._on_filter_changed(filter_name)

    def _on_add_job(self):
        """Handle add job button click."""
        dialog = AddJobDialog(self)
        if dialog.exec():
            result = dialog.get_result()
            if result:
                if result["mode"] == "url":
                    self._add_job_from_url(result["url"])
                else:
                    self._add_job_manual(result)

    def _add_job_from_url(self, url: str):
        """Fetch job details from URL and add."""
        from search_jobs import fetch_job_details

        # Fetch in background
        def fetch():
            return fetch_job_details(url)

        self.current_worker = Worker(fetch)
        self.current_worker.finished.connect(self._on_url_fetched)
        self.current_worker.error.connect(lambda e: QMessageBox.warning(self, "Error", f"Failed to fetch job: {e}"))
        self.current_worker.start()

    def _on_url_fetched(self, data: dict | None):
        """Handle fetched job data from URL."""
        if not data:
            QMessageBox.warning(self, "Error", "Could not fetch job details from URL")
            return

        job = self.user.job_handler.add(
            company=data.get("company", "Unknown Company"),
            title=data.get("title", "Unknown Title"),
            link=data.get("link", ""),
            location=data.get("location", ""),
            full_description=data.get("full_description", ""),
            description=data.get("description", ""),
            addressee=data.get("addressee"),
        )
        self.refresh()
        self.job_selected.emit(job.id)

    def _add_job_manual(self, data: dict):
        """Add job with manually entered details."""
        job = self.user.job_handler.add(
            company=data["company"],
            title=data["title"],
            link=data.get("link", ""),
            location=data.get("location", ""),
        )
        self.refresh()
        self.job_selected.emit(job.id)

    def _on_search_changed(self, text: str):
        """Handle search text changes."""
        self._refresh_jobs()

    def _get_filtered_jobs(self) -> list[Job]:
        """Get jobs filtered by current filter and search text."""
        jobs = list(self.user.job_handler)

        # Filter by status
        if self.current_filter == "pending":
            jobs = [j for j in jobs if j.status == JobStatus.PENDING]
        elif self.current_filter == "in_progress":
            jobs = [j for j in jobs if j.status == JobStatus.IN_PROGRESS]
        elif self.current_filter == "applied":
            jobs = [j for j in jobs if j.status == JobStatus.APPLIED]
        elif self.current_filter == "discarded":
            jobs = [j for j in jobs if j.status == JobStatus.DISCARDED]

        # Filter by search text
        search_text = self.search_box.text().strip().lower()
        if search_text:
            jobs = [
                j for j in jobs
                if search_text in j.title.lower()
                or search_text in j.company.lower()
                or (j.location and search_text in j.location.lower())
            ]

        return jobs

    def _refresh_jobs(self):
        """Refresh the jobs list display."""
        # Clear existing cards (but not the empty_label or stretch)
        while self.jobs_layout.count() > 1:  # Keep the stretch
            item = self.jobs_layout.takeAt(0)
            widget = item.widget()
            if widget and widget is not self.empty_label:
                widget.deleteLater()

        # Get filtered jobs
        jobs = self._get_filtered_jobs()

        if not jobs:
            self.empty_label.show()
            if self.empty_label.parent() is None:
                self.jobs_layout.insertWidget(0, self.empty_label)
        else:
            self.empty_label.hide()

            # Add job cards
            for job in jobs:
                card = JobCard(job)
                card.clicked.connect(self.job_selected)
                self.jobs_layout.insertWidget(self.jobs_layout.count() - 1, card)

    def refresh(self):
        """Refresh the entire page."""
        # Update filter counts
        job_handler = self.user.job_handler

        self.filter_buttons["all"].set_count(len(job_handler))
        self.filter_buttons["pending"].set_count(job_handler.number_pending)
        self.filter_buttons["in_progress"].set_count(job_handler.number_in_progress)
        self.filter_buttons["applied"].set_count(job_handler.number_applied)
        self.filter_buttons["discarded"].set_count(job_handler.number_discarded)

        # Refresh jobs list
        self._refresh_jobs()
