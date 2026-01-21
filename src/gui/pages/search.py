"""Search page - configure and run job searches."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QProgressBar, QCheckBox
)

from data_handlers import User
from gui.workers import Worker
from services import UserProfileService
from search_jobs import JobSearcher
from gui.styles import make_card, make_section_title, make_label
from gui.widgets import RemovableList, QueryGenerateDialog


class SearchPage(QWidget):
    """Page for configuring and running job searches."""

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.current_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Page header (no container)
        header = QLabel("Search for Jobs")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e293b; background: transparent;")
        layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # === Search Criteria Card ===
        criteria_card = make_card()
        criteria_layout = QVBoxLayout(criteria_card)
        criteria_layout.setContentsMargins(20, 20, 20, 20)
        criteria_layout.setSpacing(8)

        criteria_layout.addWidget(make_section_title("Search Criteria"))

        self.titles_label = make_label()
        criteria_layout.addWidget(self.titles_label)

        self.locations_label = make_label()
        criteria_layout.addWidget(self.locations_label)

        self.queries_count_label = make_label()
        self.queries_count_label.setStyleSheet("""
            font-size: 14px;
            color: #475569;
            font-weight: 500;
            margin-top: 8px;
            background: transparent;
            border: none;
        """)
        criteria_layout.addWidget(self.queries_count_label)

        content_layout.addWidget(criteria_card)

        # === Search Queries Card ===
        queries_card = make_card()
        queries_layout = QVBoxLayout(queries_card)
        queries_layout.setContentsMargins(20, 20, 20, 20)
        queries_layout.setSpacing(12)

        # Header with generate button
        queries_header = QHBoxLayout()
        queries_header.addWidget(make_section_title("Search Queries"))
        queries_header.addStretch()

        generate_btn = QPushButton("+ Generate New Queries")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-size: 13px;
                font-weight: 500;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        generate_btn.clicked.connect(self._show_generate_dialog)
        queries_header.addWidget(generate_btn)

        queries_layout.addLayout(queries_header)

        # Query list with checkboxes and remove buttons
        self.queries_list = RemovableList("No search queries yet", checkable=True)
        self.queries_list.item_removed.connect(self._remove_query)
        self.queries_list.selection_changed.connect(self._on_selection_changed)
        queries_layout.addWidget(self.queries_list)

        # Progress label
        self.query_progress = make_label()
        self.query_progress.setStyleSheet("font-size: 13px; color: #2563eb; background: transparent; border: none;")
        self.query_progress.hide()
        queries_layout.addWidget(self.query_progress)

        content_layout.addWidget(queries_card)

        # === Run Search Card ===
        search_card = make_card()
        search_layout = QVBoxLayout(search_card)
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_layout.setSpacing(12)

        search_layout.addWidget(make_section_title("Run Search"))

        # Options
        self.fetch_descriptions_checkbox = QCheckBox("Fetch full job descriptions (slower but more complete)")
        self.fetch_descriptions_checkbox.setChecked(True)
        self.fetch_descriptions_checkbox.setStyleSheet("font-size: 14px; color: #475569; background: transparent;")
        search_layout.addWidget(self.fetch_descriptions_checkbox)

        # Search buttons
        search_btns = QHBoxLayout()
        search_btns.setSpacing(12)

        self.search_all_btn = QPushButton("Search All Queries")
        self.search_all_btn.setMinimumHeight(44)
        self.search_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #94a3b8; }
        """)
        self.search_all_btn.clicked.connect(self._run_search_all)
        search_btns.addWidget(self.search_all_btn)

        self.search_selected_btn = QPushButton("Search Selected")
        self.search_selected_btn.setMinimumHeight(44)
        self.search_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #e2e8f0;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #e2e8f0; }
            QPushButton:disabled { background-color: #f1f5f9; color: #94a3b8; }
        """)
        self.search_selected_btn.clicked.connect(self._run_search_selected)
        self.search_selected_btn.setEnabled(False)
        search_btns.addWidget(self.search_selected_btn)

        search_btns.addStretch()
        search_layout.addLayout(search_btns)

        # Progress
        self.search_progress = QProgressBar()
        self.search_progress.setTextVisible(False)
        self.search_progress.setMinimum(0)
        self.search_progress.setMaximum(0)
        self.search_progress.hide()
        search_layout.addWidget(self.search_progress)

        self.search_status = make_label()
        self.search_status.setStyleSheet("font-size: 14px; color: #2563eb; background: transparent; border: none;")
        self.search_status.hide()
        search_layout.addWidget(self.search_status)

        content_layout.addWidget(search_card)

        # Results banner (shown after search)
        self.results_card = QFrame()
        self.results_card.setStyleSheet("""
            QFrame {
                background-color: #dcfce7;
                border: 1px solid #bbf7d0;
                border-radius: 12px;
            }
        """)
        self.results_card.hide()

        results_layout = QVBoxLayout(self.results_card)
        results_layout.setContentsMargins(20, 16, 20, 16)
        self.results_label = QLabel()
        self.results_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #166534; background: transparent;")
        results_layout.addWidget(self.results_label)

        content_layout.addWidget(self.results_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _show_generate_dialog(self):
        """Show dialog for generating queries."""
        dialog = QueryGenerateDialog(self)
        if dialog.exec():
            self._generate_queries(dialog.selected_count, dialog.replace_existing)

    def _generate_queries(self, num_queries: int, replace_existing: bool = False):
        if replace_existing:
            # Clear existing queries first
            self.user.query_handler.clear()
            self.refresh()

        self.query_progress.show()
        self.query_progress.setText(f"Generating {num_queries} queries...")

        service = UserProfileService(self.user)

        def generate():
            return service.create_search_queries(num_queries=num_queries)

        self.current_worker = Worker(generate)
        self.current_worker.progress.connect(lambda msg, _: self.query_progress.setText(msg))
        self.current_worker.finished.connect(self._on_queries_generated)
        self.current_worker.error.connect(self._on_query_error)
        self.current_worker.start()

    def _on_queries_generated(self, result):
        self.query_progress.hide()
        if result.success:
            QMessageBox.information(self, "Success", result.message)
        else:
            QMessageBox.warning(self, "Warning", result.message)
        self.refresh()

    def _on_query_error(self, error: str):
        self.query_progress.hide()
        QMessageBox.critical(self, "Error", f"Failed to generate queries: {error}")

    def _remove_query(self, query_id: str):
        """Remove a single query by ID."""
        self.user.query_handler.remove([query_id])
        self.refresh()

    def _on_selection_changed(self):
        """Update Search Selected button state based on selection."""
        has_selection = self.queries_list.has_selection()
        self.search_selected_btn.setEnabled(has_selection)

    def _run_search_all(self):
        if len(self.user.query_handler) == 0:
            QMessageBox.warning(self, "No Queries", "Please generate search queries first")
            return
        self._start_search(query_ids=None)

    def _run_search_selected(self):
        selected_ids = self.queries_list.get_selected_ids()
        if not selected_ids:
            QMessageBox.information(self, "Info", "Please select queries to search with")
            return
        self._start_search(query_ids=selected_ids)

    def _start_search(self, query_ids=None):
        self.search_progress.show()
        self.search_status.show()
        self.search_status.setText("Starting search...")
        self.search_all_btn.setEnabled(False)
        self.search_selected_btn.setEnabled(False)
        self.results_card.hide()

        fetch_descriptions = self.fetch_descriptions_checkbox.isChecked()
        searcher = JobSearcher(user=self.user)

        def run_search():
            return searcher.search(query_ids=query_ids, fetch_descriptions=fetch_descriptions)

        self.current_worker = Worker(run_search)
        self.current_worker.progress.connect(lambda msg, _: self.search_status.setText(msg))
        self.current_worker.finished.connect(self._on_search_finished)
        self.current_worker.error.connect(self._on_search_error)
        self.current_worker.start()

    def _on_search_finished(self, result):
        self.search_progress.hide()
        self.search_status.hide()
        self.search_all_btn.setEnabled(True)
        self.search_selected_btn.setEnabled(self.queries_list.has_selection())

        self.results_label.setText(f"Search complete! Found {self.user.job_handler.number_pending} new pending jobs.")
        self.results_card.show()
        self.refresh()

    def _on_search_error(self, error: str):
        self.search_progress.hide()
        self.search_status.hide()
        self.search_all_btn.setEnabled(True)
        self.search_selected_btn.setEnabled(self.queries_list.has_selection())
        QMessageBox.critical(self, "Error", f"Search failed: {error}")

    def refresh(self):
        titles = self.user.desired_job_titles
        self.titles_label.setText(f"Job Titles: {', '.join(titles)}" if titles else "Job Titles: Not configured")

        locations = self.user.desired_job_locations
        self.locations_label.setText(f"Locations: {', '.join(locations)}" if locations else "Locations: Not configured")

        num_queries = len(self.user.query_handler)
        self.queries_count_label.setText(f"{num_queries} search queries configured")

        # Update query list - use set_items_with_ids for queries with IDs
        self.queries_list.set_items_with_ids(list(self.user.query_handler))

        self.search_all_btn.setEnabled(num_queries > 0)
