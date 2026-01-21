"""Profile page - view and edit user information."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QFileDialog, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt

from data_handlers import User
from gui.workers import Worker
from services import UserProfileService
from gui.styles import make_card, make_section_title, make_label, make_primary_button, make_secondary_button
from gui.widgets import TagContainer, RemovableList, FieldRow, CredentialsDialog


class ProfilePage(QWidget):
    """Page for viewing and editing user profile."""

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.current_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Page header
        header = QLabel("Profile")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e293b; background: transparent; border: none;")
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

        # === Basic Information Card ===
        basic_card = make_card()
        basic_layout = QVBoxLayout(basic_card)
        basic_layout.setContentsMargins(20, 20, 20, 20)
        basic_layout.setSpacing(12)

        basic_layout.addWidget(make_section_title("Basic Information"))

        self.name_field = FieldRow("Name")
        self.name_field.value_changed.connect(lambda v: setattr(self.user, 'name', v))
        basic_layout.addWidget(self.name_field)

        self.email_field = FieldRow("Email")
        self.email_field.value_changed.connect(lambda v: setattr(self.user, 'email', v))
        basic_layout.addWidget(self.email_field)

        # Credentials row
        creds_row = QHBoxLayout()
        creds_row.setSpacing(12)
        creds_label = QLabel("Credentials:")
        creds_label.setStyleSheet("font-size: 14px; color: #64748b; background: transparent; border: none; padding: 0; margin: 0; min-width: 80px;")
        creds_row.addWidget(creds_label)

        self.credentials_tags = TagContainer()
        self.credentials_tags.tag_removed.connect(self._remove_credential)
        creds_row.addWidget(self.credentials_tags, 1)

        add_cred_btn = make_primary_button("+ Add")
        add_cred_btn.clicked.connect(self._add_credential)
        creds_row.addWidget(add_cred_btn)
        basic_layout.addLayout(creds_row)

        content_layout.addWidget(basic_card)

        # === Job Titles Card ===
        titles_card = make_card()
        titles_layout = QVBoxLayout(titles_card)
        titles_layout.setContentsMargins(20, 20, 20, 20)
        titles_layout.setSpacing(12)

        titles_header = QHBoxLayout()
        titles_header.addWidget(make_section_title("Job Titles"))
        titles_header.addStretch()
        add_title_btn = make_primary_button("+ Add")
        add_title_btn.clicked.connect(self._add_title)
        titles_header.addWidget(add_title_btn)
        titles_layout.addLayout(titles_header)

        self.titles_tags = TagContainer()
        self.titles_tags.tag_removed.connect(self._remove_title)
        titles_layout.addWidget(self.titles_tags)

        content_layout.addWidget(titles_card)

        # === Locations Card ===
        locations_card = make_card()
        locations_layout = QVBoxLayout(locations_card)
        locations_layout.setContentsMargins(20, 20, 20, 20)
        locations_layout.setSpacing(12)

        locations_header = QHBoxLayout()
        locations_header.addWidget(make_section_title("Locations"))
        locations_header.addStretch()
        add_location_btn = make_primary_button("+ Add")
        add_location_btn.clicked.connect(self._add_location)
        locations_header.addWidget(add_location_btn)
        locations_layout.addLayout(locations_header)

        self.locations_tags = TagContainer()
        self.locations_tags.tag_removed.connect(self._remove_location)
        locations_layout.addWidget(self.locations_tags)

        content_layout.addWidget(locations_card)

        # === Search Instructions Card ===
        search_instr_card = make_card()
        search_instr_layout = QVBoxLayout(search_instr_card)
        search_instr_layout.setContentsMargins(20, 20, 20, 20)
        search_instr_layout.setSpacing(12)

        search_instr_header = QHBoxLayout()
        search_instr_header.addWidget(make_section_title("Search Instructions"))
        search_instr_header.addStretch()
        add_search_instr_btn = make_primary_button("+ Add")
        add_search_instr_btn.clicked.connect(self._add_search_instruction)
        search_instr_header.addWidget(add_search_instr_btn)
        search_instr_layout.addLayout(search_instr_header)

        search_instr_layout.addWidget(make_label("Guide AI when generating search queries and filtering job results"))

        self.search_instructions_list = RemovableList("No search instructions added yet")
        self.search_instructions_list.item_removed.connect(self._remove_search_instruction)
        search_instr_layout.addWidget(self.search_instructions_list)

        content_layout.addWidget(search_instr_card)

        # === Online Presence Card ===
        online_card = make_card()
        online_layout = QVBoxLayout(online_card)
        online_layout.setContentsMargins(20, 20, 20, 20)
        online_layout.setSpacing(12)

        online_header = QHBoxLayout()
        online_header.addWidget(make_section_title("Online Presence"))
        online_header.addStretch()
        add_website_btn = make_primary_button("+ Add")
        add_website_btn.clicked.connect(self._add_website)
        online_header.addWidget(add_website_btn)
        online_layout.addLayout(online_header)

        online_layout.addWidget(make_label("LinkedIn, GitHub, portfolio sites"))

        self.websites_list = RemovableList("No websites added yet")
        self.websites_list.item_removed.connect(self._remove_website)
        online_layout.addWidget(self.websites_list)

        refresh_online_btn = make_secondary_button("Refresh Online Presence")
        refresh_online_btn.clicked.connect(self._refresh_online_presence)
        online_layout.addWidget(refresh_online_btn, alignment=Qt.AlignLeft)

        content_layout.addWidget(online_card)

        # === Source Documents Card ===
        docs_card = make_card()
        docs_layout = QVBoxLayout(docs_card)
        docs_layout.setContentsMargins(20, 20, 20, 20)
        docs_layout.setSpacing(12)

        docs_header = QHBoxLayout()
        docs_header.addWidget(make_section_title("Source Documents"))
        docs_header.addStretch()
        add_file_btn = make_primary_button("+ File")
        add_file_btn.clicked.connect(self._add_source_file)
        docs_header.addWidget(add_file_btn)
        add_folder_btn = make_secondary_button("+ Folder")
        add_folder_btn.clicked.connect(self._add_source_folder)
        docs_header.addWidget(add_folder_btn)
        docs_layout.addLayout(docs_header)

        docs_layout.addWidget(make_label("CVs, resumes, cover letters - used to generate your professional summary"))

        self.docs_list = RemovableList("No documents added yet")
        self.docs_list.item_removed.connect(self._remove_source_doc)
        docs_layout.addWidget(self.docs_list)

        content_layout.addWidget(docs_card)

        # === Professional Summary Card ===
        summary_card = make_card()
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(20, 20, 20, 20)
        summary_layout.setSpacing(12)

        # Header with title and generate button
        summary_header = QHBoxLayout()
        summary_header.addWidget(make_section_title("Professional Summary"))
        summary_header.addStretch()

        self.generate_summary_btn = make_primary_button("Generate")
        self.generate_summary_btn.clicked.connect(self._generate_summary)
        summary_header.addWidget(self.generate_summary_btn)

        summary_layout.addLayout(summary_header)

        self.summary_status = make_label()
        summary_layout.addWidget(self.summary_status)

        self.summary_text = QLabel()
        self.summary_text.setWordWrap(True)
        self.summary_text.setStyleSheet("""
            font-size: 14px;
            color: #374151;
            line-height: 1.6;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        self.summary_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        summary_layout.addWidget(self.summary_text)

        self.summary_progress = make_label()
        self.summary_progress.setStyleSheet("font-size: 13px; color: #2563eb; background: transparent; border: none;")
        self.summary_progress.hide()
        summary_layout.addWidget(self.summary_progress)

        content_layout.addWidget(summary_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    # === Event handlers ===

    def _add_title(self):
        text, ok = QInputDialog.getText(self, "Add Job Title", "Job title:")
        if ok and text:
            self.user.add_desired_job_title(text)
            self.refresh()

    def _remove_title(self, title: str):
        self.user.remove_desired_job_title(title)
        self.refresh()

    def _add_location(self):
        text, ok = QInputDialog.getText(self, "Add Location", "Location:")
        if ok and text:
            self.user.add_desired_job_location(text)
            self.refresh()

    def _remove_location(self, location: str):
        self.user.remove_desired_job_location(location)
        self.refresh()

    def _add_credential(self):
        existing = self.user.credentials or []
        dialog = CredentialsDialog(existing_credentials=existing, parent=self)
        if dialog.exec():
            credential = dialog.get_credential()
            if credential:
                self.user.add_credential(credential)
                self.refresh()

    def _remove_credential(self, credential: str):
        self.user.remove_credential(credential)
        self.refresh()

    def _add_search_instruction(self):
        text, ok = QInputDialog.getText(self, "Add Search Instruction", "Instruction:")
        if ok and text:
            instructions = self.user.search_instructions or []
            instructions.append(text.strip())
            self.user.search_instructions = instructions
            self.refresh()

    def _remove_search_instruction(self, instruction: str):
        instructions = list(self.user.search_instructions or [])
        if instruction in instructions:
            instructions.remove(instruction)
            self.user.search_instructions = instructions
            self.refresh()

    def _add_website(self):
        text, ok = QInputDialog.getText(self, "Add Website", "URL:")
        if ok and text:
            self.user.add_website(text)
            self.refresh()

    def _remove_website(self, url: str):
        self.user.remove_website(url)
        self.refresh()

    def _add_source_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Source Document", "",
            "Documents (*.pdf *.docx *.doc *.txt *.tex);;All Files (*)"
        )
        if file_path:
            self.user.add_source_document_path(file_path)
            self.refresh()

    def _add_source_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.user.add_source_document_path(f"{folder_path}/*")
            self.refresh()

    def _remove_source_doc(self, path: str):
        self.user.remove_source_document_path(path)
        self.refresh()

    def _refresh_online_presence(self):
        service = UserProfileService(self.user)
        result = service.refresh_online_presence()
        if result.success:
            QMessageBox.information(self, "Success", result.message)
        else:
            QMessageBox.warning(self, "Warning", result.message)
        self.refresh()

    def _generate_summary(self):
        self.summary_progress.show()
        self.summary_progress.setText("Generating summary...")

        service = UserProfileService(self.user)
        self.current_worker = Worker(service.generate_comprehensive_summary)
        self.current_worker.progress.connect(lambda msg, _: self.summary_progress.setText(msg))
        self.current_worker.finished.connect(self._on_summary_finished)
        self.current_worker.error.connect(self._on_summary_error)
        self.current_worker.start()

    def _on_summary_finished(self, result):
        self.summary_progress.hide()
        if result.success:
            QMessageBox.information(self, "Success", result.message)
        else:
            QMessageBox.warning(self, "Warning", result.message)
        self.refresh()

    def _on_summary_error(self, error: str):
        self.summary_progress.hide()
        QMessageBox.critical(self, "Error", f"Failed to generate summary: {error}")

    def refresh(self):
        """Refresh page with current user data."""
        self.name_field.set_value(self.user.name or "")
        self.email_field.set_value(self.user.email or "")
        self.credentials_tags.set_tags(self.user.credentials or [])

        self.titles_tags.set_tags(self.user.desired_job_titles)
        self.locations_tags.set_tags(self.user.desired_job_locations)

        self.search_instructions_list.set_items(self.user.search_instructions or [])

        self.websites_list.set_items(self.user.websites)
        self.docs_list.set_items(self.user.source_document_paths)

        if self.user.comprehensive_summary:
            self.summary_status.hide()
            self.generate_summary_btn.setText("Regenerate")
            self.summary_text.setText(self.user.comprehensive_summary)
            self.summary_text.show()
        else:
            self.summary_status.setText("No summary generated yet")
            self.summary_status.show()
            self.generate_summary_btn.setText("Generate")
            self.summary_text.hide()
