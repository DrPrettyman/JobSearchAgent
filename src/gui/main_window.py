"""Main application window with top navigation."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from data_handlers import User


class NavButton(QPushButton):
    """A styled top navigation button."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)


class MainWindow(QMainWindow):
    """Main application window with top navigation."""

    def __init__(self, user: User):
        super().__init__()
        self.user = user

        self.setWindowTitle(f"JobSearch - {user.name or user.username}")
        self.setMinimumSize(700, 400)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout (vertical: navbar on top, content below)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top navbar
        self.navbar = self._create_navbar()
        main_layout.addWidget(self.navbar)

        # Content area
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("content_area")
        main_layout.addWidget(self.content_stack)

        # Create pages (imported here to avoid circular imports)
        from gui.pages.dashboard import DashboardPage
        from gui.pages.jobs_list import JobsListPage
        from gui.pages.job_detail import JobDetailPage
        from gui.pages.profile import ProfilePage
        from gui.pages.search import SearchPage

        # Initialize pages
        self.dashboard_page = DashboardPage(user, self)
        self.jobs_page = JobsListPage(user, self)
        self.job_detail_page = JobDetailPage(user, self)
        self.profile_page = ProfilePage(user, self)
        self.search_page = SearchPage(user, self)

        # Add pages to stack
        self.content_stack.addWidget(self.dashboard_page)  # 0
        self.content_stack.addWidget(self.jobs_page)       # 1
        self.content_stack.addWidget(self.job_detail_page) # 2
        self.content_stack.addWidget(self.profile_page)    # 3
        self.content_stack.addWidget(self.search_page)     # 4

        # Connect job list to job detail
        self.jobs_page.job_selected.connect(self.show_job_detail)
        self.job_detail_page.back_requested.connect(self.show_jobs_list)

        # Connect dashboard quick actions
        self.dashboard_page.navigate_to.connect(self._handle_navigation)

        # Show dashboard by default
        self._show_page(0)
        self.nav_buttons[0].setChecked(True)

    def _create_navbar(self) -> QWidget:
        """Create the top navbar with navigation buttons."""
        navbar = QFrame()
        navbar.setObjectName("navbar")
        navbar.setFixedHeight(56)

        layout = QHBoxLayout(navbar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)

        # App title/logo
        header = QLabel("JobSearch")
        header.setObjectName("navbar_header")
        layout.addWidget(header)

        layout.addSpacing(32)

        # Navigation buttons
        self.nav_buttons = []

        nav_items = ["Dashboard", "Jobs", "Search", "Profile"]

        for i, text in enumerate(nav_items):
            btn = NavButton(text)
            btn.clicked.connect(lambda checked, idx=i: self._on_nav_clicked(idx))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Spacer to push user info to the right
        layout.addStretch()

        # User info on the right
        user_label = QLabel(self.user.name or self.user.username)
        user_label.setObjectName("navbar_user")
        layout.addWidget(user_label)

        return navbar

    def _on_nav_clicked(self, index: int):
        """Handle navigation button clicks."""
        # Map navigation indices to page indices
        # Nav: Dashboard(0), Jobs(1), Search(2), Profile(3)
        # Pages: Dashboard(0), Jobs(1), JobDetail(2), Profile(3), Search(4)
        page_map = {
            0: 0,  # Dashboard
            1: 1,  # Jobs
            2: 4,  # Search
            3: 3,  # Profile
        }
        self._show_page(page_map[index])

        # Update button states
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def _show_page(self, index: int):
        """Show a specific page by index."""
        self.content_stack.setCurrentIndex(index)

        # Refresh page data when shown
        current = self.content_stack.currentWidget()
        if hasattr(current, 'refresh'):
            current.refresh()

    def _handle_navigation(self, destination: str):
        """Handle navigation requests from pages."""
        nav_map = {
            "dashboard": 0,
            "jobs": 1,
            "jobs_pending": 1,
            "jobs_in_progress": 1,
            "jobs_applied": 1,
            "jobs_discarded": 1,
            "search": 2,
            "profile": 3,
        }

        if destination in nav_map:
            nav_index = nav_map[destination]
            self._on_nav_clicked(nav_index)

            # Set filter if specific job status requested
            if destination.startswith("jobs_"):
                status = destination.replace("jobs_", "")
                self.jobs_page.set_filter(status)

    def show_job_detail(self, job_id: str):
        """Navigate to job detail page for a specific job."""
        self.job_detail_page.set_job(job_id)
        self.content_stack.setCurrentIndex(2)

        # Update nav button states (Jobs should appear selected)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == 1)

    def show_jobs_list(self):
        """Navigate back to jobs list."""
        self._on_nav_clicked(1)

    def refresh_all(self):
        """Refresh all pages."""
        for i in range(self.content_stack.count()):
            page = self.content_stack.widget(i)
            if hasattr(page, 'refresh'):
                page.refresh()
