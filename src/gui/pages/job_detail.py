"""Job detail page - view and manage a single job."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit, QMessageBox, QInputDialog, QApplication
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices

import webbrowser
import urllib.parse

from data_handlers import User, Job, JobStatus
from gui.widgets.status_badge import StatusBadge
from gui.widgets import RemovableList, FieldRow, TextEditDialog, AddQuestionsDialog
from gui.workers import Worker
from services import CoverLetterService
from gui.styles import make_card, make_section_title, make_label, make_secondary_button
from question_answerer import generate_answers_batch
from utils import combined_documents_as_string


class JobDetailPage(QWidget):
    """Detailed view of a single job with actions."""

    back_requested = Signal()

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.job = None
        self.current_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Back button row
        back_row = QHBoxLayout()
        back_btn = QPushButton("< Back to Jobs")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2563eb;
                border: none;
                padding: 8px 0;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #1d4ed8;
                text-decoration: underline;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.back_requested)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        content_layout.addWidget(self._create_header_card())
        content_layout.addWidget(self._create_status_card())
        content_layout.addWidget(self._create_edit_details_card())
        content_layout.addWidget(self._create_description_card())
        content_layout.addWidget(self._create_questions_card())
        content_layout.addWidget(self._create_instructions_card())
        content_layout.addWidget(self._create_cover_letter_card())

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_header_card(self) -> QWidget:
        """Create the header card with job title, company, and basic info."""
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # Title and status row
        title_row = QHBoxLayout()

        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        self.title_label.setWordWrap(True)
        title_row.addWidget(self.title_label, 1)

        self.status_badge = StatusBadge()
        title_row.addWidget(self.status_badge)

        layout.addLayout(title_row)

        # Company
        self.company_label = QLabel()
        self.company_label.setStyleSheet("""
            font-size: 18px;
            color: #2563eb;
            font-weight: 500;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        layout.addWidget(self.company_label)

        # Location
        self.location_label = make_label()
        layout.addWidget(self.location_label)

        # Date
        self.date_label = make_label()
        layout.addWidget(self.date_label)

        # Action buttons row
        action_btns = QHBoxLayout()
        action_btns.setSpacing(8)

        self.link_btn = make_secondary_button("Open Link")
        self.link_btn.clicked.connect(self._open_job_link)
        action_btns.addWidget(self.link_btn)

        google_btn = make_secondary_button("Google This Job")
        google_btn.clicked.connect(self._google_job)
        action_btns.addWidget(google_btn)

        action_btns.addStretch()
        layout.addLayout(action_btns)

        # Short description (from scraping)
        self.short_desc_label = QLabel()
        self.short_desc_label.setWordWrap(True)
        self.short_desc_label.setStyleSheet("""
            font-size: 14px;
            color: #64748b;
            background: transparent;
            border: none;
            padding: 8px 0 0 0;
            margin: 0;
        """)
        self.short_desc_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.short_desc_label)

        return card

    def _create_status_card(self) -> QWidget:
        """Create the status actions card with status change buttons."""
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(make_section_title("Update Status"))

        status_btns = QHBoxLayout()
        status_btns.setSpacing(8)

        self.pending_btn = QPushButton("Pending")
        self.pending_btn.setStyleSheet("""
            QPushButton { background-color: #fef3c7; color: #92400e; border: none; padding: 8px 16px; border-radius: 6px; }
            QPushButton:hover { background-color: #fde68a; }
        """)
        self.pending_btn.clicked.connect(lambda: self._set_status(JobStatus.PENDING))
        status_btns.addWidget(self.pending_btn)

        self.progress_btn = QPushButton("In Progress")
        self.progress_btn.setStyleSheet("""
            QPushButton { background-color: #cffafe; color: #155e75; border: none; padding: 8px 16px; border-radius: 6px; }
            QPushButton:hover { background-color: #a5f3fc; }
        """)
        self.progress_btn.clicked.connect(lambda: self._set_status(JobStatus.IN_PROGRESS))
        status_btns.addWidget(self.progress_btn)

        self.applied_btn = QPushButton("Applied")
        self.applied_btn.setStyleSheet("""
            QPushButton { background-color: #dcfce7; color: #166534; border: none; padding: 8px 16px; border-radius: 6px; }
            QPushButton:hover { background-color: #bbf7d0; }
        """)
        self.applied_btn.clicked.connect(lambda: self._set_status(JobStatus.APPLIED))
        status_btns.addWidget(self.applied_btn)

        self.discard_btn = QPushButton("Discard")
        self.discard_btn.setStyleSheet("""
            QPushButton { background-color: #fee2e2; color: #991b1b; border: none; padding: 8px 16px; border-radius: 6px; }
            QPushButton:hover { background-color: #fecaca; }
        """)
        self.discard_btn.clicked.connect(lambda: self._set_status(JobStatus.DISCARDED))
        status_btns.addWidget(self.discard_btn)

        status_btns.addStretch()
        layout.addLayout(status_btns)

        return card

    def _create_edit_details_card(self) -> QWidget:
        """Create the edit details card with editable job fields."""
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        layout.addWidget(make_section_title("Edit Job Details"))

        self.company_field = FieldRow("Company")
        self.company_field.value_changed.connect(self._on_company_changed)
        layout.addWidget(self.company_field)

        self.title_field = FieldRow("Title")
        self.title_field.value_changed.connect(self._on_title_changed)
        layout.addWidget(self.title_field)

        self.location_field = FieldRow("Location")
        self.location_field.value_changed.connect(self._on_location_changed)
        layout.addWidget(self.location_field)

        self.link_field = FieldRow("Job URL")
        self.link_field.value_changed.connect(self._on_link_changed)
        layout.addWidget(self.link_field)

        self.addressee_field = FieldRow("Hiring Manager")
        self.addressee_field.value_changed.connect(self._on_addressee_changed)
        layout.addWidget(self.addressee_field)

        return card

    def _create_description_card(self) -> QWidget:
        """Create the job description card with view/edit buttons."""
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header with buttons
        header = QHBoxLayout()
        self.full_desc_title = make_section_title("Full Job Description")
        header.addWidget(self.full_desc_title)
        header.addStretch()

        self.edit_desc_btn = make_secondary_button("Edit")
        self.edit_desc_btn.clicked.connect(self._edit_description)
        header.addWidget(self.edit_desc_btn)

        layout.addLayout(header)

        self.desc_text = QLabel()
        self.desc_text.setWordWrap(True)
        self.desc_text.setStyleSheet("""
            font-size: 14px;
            color: #374151;
            line-height: 1.6;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        self.desc_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.desc_text)

        return card

    def _create_questions_card(self) -> QWidget:
        """Create the application questions card."""
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header with buttons
        header = QHBoxLayout()
        self.questions_title = make_section_title("Application Questions")
        header.addWidget(self.questions_title)
        header.addStretch()

        self.add_questions_btn = QPushButton("Add Questions")
        self.add_questions_btn.setStyleSheet("""
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
        self.add_questions_btn.clicked.connect(self._add_questions)
        header.addWidget(self.add_questions_btn)

        self.generate_answers_btn = make_secondary_button("Generate Answers")
        self.generate_answers_btn.clicked.connect(self._generate_answers)
        header.addWidget(self.generate_answers_btn)

        self.clear_questions_btn = make_secondary_button("Clear All")
        self.clear_questions_btn.clicked.connect(self._clear_questions)
        header.addWidget(self.clear_questions_btn)

        layout.addLayout(header)

        # Questions container
        self.questions_container = QWidget()
        self.questions_container_layout = QVBoxLayout(self.questions_container)
        self.questions_container_layout.setContentsMargins(0, 0, 0, 0)
        self.questions_container_layout.setSpacing(16)
        layout.addWidget(self.questions_container)

        # Progress label for answer generation
        self.questions_progress = make_label()
        self.questions_progress.setStyleSheet("""
            font-size: 13px;
            color: #2563eb;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        self.questions_progress.hide()
        layout.addWidget(self.questions_progress)

        return card

    def _create_instructions_card(self) -> QWidget:
        """Create the writing instructions card."""
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(make_section_title("Writing Instructions"))

        # General instructions (read-only)
        self.general_instructions_label = make_label("General instructions from profile:")
        layout.addWidget(self.general_instructions_label)

        self.general_instructions_text = QLabel()
        self.general_instructions_text.setWordWrap(True)
        self.general_instructions_text.setStyleSheet("""
            font-size: 13px;
            color: #64748b;
            background: transparent;
            border: none;
            padding: 4px 0 8px 12px;
            margin: 0;
        """)
        layout.addWidget(self.general_instructions_text)

        # Job-specific instructions header
        job_instr_header = QHBoxLayout()
        job_instr_header.addWidget(make_label("Job-specific instructions:"), 1)

        add_instruction_btn = QPushButton("+ Add")
        add_instruction_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2563eb;
                border: none;
                padding: 4px 8px;
                font-size: 13px;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        add_instruction_btn.setCursor(Qt.PointingHandCursor)
        add_instruction_btn.clicked.connect(self._add_writing_instruction)
        job_instr_header.addWidget(add_instruction_btn)

        layout.addLayout(job_instr_header)

        # Job-specific instructions list
        self.job_instructions_list = RemovableList("No job-specific instructions")
        self.job_instructions_list.item_removed.connect(self._remove_writing_instruction)
        layout.addWidget(self.job_instructions_list)

        return card

    def _create_cover_letter_card(self) -> QWidget:
        """Create the cover letter card with generation and viewing options."""
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header with title and generate button
        header = QHBoxLayout()
        header.addWidget(make_section_title("Cover Letter"))
        header.addStretch()

        self.generate_btn = QPushButton("Generate Cover Letter")
        self.generate_btn.setStyleSheet("""
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
            QPushButton:disabled { background-color: #94a3b8; }
        """)
        self.generate_btn.clicked.connect(self._generate_cover_letter)
        header.addWidget(self.generate_btn)

        layout.addLayout(header)

        self.cover_status = make_label()
        layout.addWidget(self.cover_status)

        # Cover letter text display
        self.cover_letter_text = QLabel()
        self.cover_letter_text.setWordWrap(True)
        self.cover_letter_text.setStyleSheet("""
            font-size: 14px;
            color: #374151;
            line-height: 1.6;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        self.cover_letter_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.cover_letter_text)

        btns = QHBoxLayout()
        btns.setSpacing(8)

        self.edit_cover_btn = make_secondary_button("Edit")
        self.edit_cover_btn.clicked.connect(self._edit_cover_letter)
        btns.addWidget(self.edit_cover_btn)

        self.copy_text_btn = make_secondary_button("Copy Text")
        self.copy_text_btn.clicked.connect(self._copy_cover_letter_text)
        btns.addWidget(self.copy_text_btn)

        self.open_pdf_btn = make_secondary_button("Open PDF")
        self.open_pdf_btn.clicked.connect(self._open_pdf)
        btns.addWidget(self.open_pdf_btn)

        self.copy_path_btn = make_secondary_button("Copy PDF Path")
        self.copy_path_btn.clicked.connect(self._copy_pdf_path)
        btns.addWidget(self.copy_path_btn)

        btns.addStretch()
        layout.addLayout(btns)

        # Progress label for generation
        self.progress_label = make_label()
        self.progress_label.setStyleSheet("""
            font-size: 13px;
            color: #2563eb;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        self.progress_label.hide()
        layout.addWidget(self.progress_label)

        return card

    def set_job(self, job_id: str):
        """Set the job to display."""
        self.job = self.user.job_handler[job_id]
        self.refresh()

    def refresh(self):
        """Refresh the page with current job data."""
        if self.job is None:
            return

        # Header info
        self.title_label.setText(self.job.title)
        self.company_label.setText(self.job.company)
        self.location_label.setText(f"Location: {self.job.location or 'Not specified'}")
        self.date_label.setText(f"Found: {self.job.date_found[:10] if self.job.date_found else 'Unknown'}")
        self.status_badge.set_status(self.job.status)

        # Link button
        # Show/hide link button based on whether there's a link
        self.link_btn.setVisible(bool(self.job.link))

        # Edit fields
        self.company_field.set_value(self.job.company or "")
        self.title_field.set_value(self.job.title or "")
        self.location_field.set_value(self.job.location or "")
        self.link_field.set_value(self.job.link or "")
        self.addressee_field.set_value(self.job.addressee or "")

        # Short description (in header)
        short_desc = self.job.description or ""
        if short_desc:
            self.short_desc_label.setText(short_desc)
            self.short_desc_label.show()
        else:
            self.short_desc_label.hide()

        # Full description card
        full_desc = self.job.full_description or ""
        if full_desc:
            self.edit_desc_btn.setText("Edit")
            self.desc_text.setText(full_desc)
        else:
            self.edit_desc_btn.setText("Add")
            self.desc_text.setText("No full description added yet. Click 'Add' to paste one.")

        # Questions
        self._refresh_questions()

        # Writing instructions
        general_instructions = self.user.cover_letter_writing_instructions
        if general_instructions:
            self.general_instructions_text.setText("• " + "\n• ".join(general_instructions))
        else:
            self.general_instructions_text.setText("None configured")

        job_instructions = self.job.writing_instructions or []
        self.job_instructions_list.set_items(job_instructions)

        # Cover letter
        if self.job.cover_letter_body:
            self.cover_status.hide()
            self.generate_btn.setText("Regenerate")
            full_text = self.job.cover_letter_full_text(
                name_for_letter=self.user.name_with_credentials
            )
            self.cover_letter_text.setText(full_text)
            self.cover_letter_text.show()
            self.edit_cover_btn.show()
            self.copy_text_btn.show()
        else:
            self.cover_status.setText("No cover letter generated yet")
            self.cover_status.show()
            self.generate_btn.setText("Generate")
            self.cover_letter_text.hide()
            self.edit_cover_btn.hide()
            self.copy_text_btn.hide()

        # PDF button
        if self.job.cover_letter_pdf_path:
            self.open_pdf_btn.show()
            self.copy_path_btn.show()
        else:
            self.open_pdf_btn.hide()
            self.copy_path_btn.hide()

    def _refresh_questions(self):
        """Refresh the questions display."""
        # Clear existing question widgets
        while self.questions_container_layout.count():
            item = self.questions_container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        questions = self.job.questions if self.job is not None else []

        # Update title with count
        count = len(questions)
        if count > 0:
            self.questions_title.setText(f"Application Questions ({count})")
        else:
            self.questions_title.setText("Application Questions")

        # Show/hide buttons based on whether there are questions
        has_questions = count > 0
        self.generate_answers_btn.setVisible(has_questions)
        self.clear_questions_btn.setVisible(has_questions)

        if not questions:
            empty_label = make_label("No questions added yet")
            self.questions_container_layout.addWidget(empty_label)
            return

        # Add Q&A widgets
        for i, qa in enumerate(questions, 1):
            qa_widget = QWidget()
            qa_layout = QVBoxLayout(qa_widget)
            qa_layout.setContentsMargins(0, 0, 0, 0)
            qa_layout.setSpacing(4)

            # Question label
            q_label = QLabel(f"Q{i}: {qa['question']}")
            q_label.setWordWrap(True)
            q_label.setStyleSheet("""
                font-size: 14px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            """)
            qa_layout.addWidget(q_label)

            # Answer label
            answer = qa.get('answer', '')
            if answer:
                a_label = QLabel(answer)
                a_label.setWordWrap(True)
                a_label.setStyleSheet("""
                    font-size: 13px;
                    color: #374151;
                    background: transparent;
                    border: none;
                    padding: 4px 0 0 12px;
                    margin: 0;
                """)
                a_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            else:
                a_label = QLabel("(no answer generated)")
                a_label.setStyleSheet("""
                    font-size: 13px;
                    color: #94a3b8;
                    font-style: italic;
                    background: transparent;
                    border: none;
                    padding: 4px 0 0 12px;
                    margin: 0;
                """)
            qa_layout.addWidget(a_label)

            self.questions_container_layout.addWidget(qa_widget)

    def _set_status(self, status: JobStatus):
        """Update job status."""
        if self.job is not None:
            self.job.status = status
            self.refresh()

    def _open_job_link(self):
        """Open job posting in browser."""
        if self.job is not None and self.job.link:
            webbrowser.open(self.job.link)

    def _google_job(self):
        """Search for job on Google."""
        if self.job is not None:
            query = urllib.parse.quote(f"careers {self.job.company} {self.job.title}")
            webbrowser.open(f"https://www.google.com/search?q={query}")

    def _generate_cover_letter(self):
        """Generate cover letter in background thread."""
        if self.job is None:
            return

        # Disable button during generation
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("Generating...")
        self.progress_label.show()
        self.progress_label.setText("Starting generation...")

        # Create service and worker
        service = CoverLetterService(
            job=self.job,
            user=self.user,
        )

        self.current_worker = Worker(service.generate)
        self.current_worker.progress.connect(self._on_progress)
        self.current_worker.finished.connect(self._on_generation_finished)
        self.current_worker.error.connect(self._on_generation_error)
        self.current_worker.start()

    def _on_progress(self, message: str, level: str):
        """Handle progress updates."""
        self.progress_label.setText(message)

    def _on_generation_finished(self, result):
        """Handle generation completion."""
        self.generate_btn.setEnabled(True)
        self.progress_label.hide()

        if result.success:
            QMessageBox.information(self, "Success", "Cover letter generated successfully!")
        else:
            QMessageBox.warning(self, "Warning", result.message)

        self.refresh()

    def _on_generation_error(self, error: str):
        """Handle generation error."""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generate Cover Letter")
        self.progress_label.hide()
        QMessageBox.critical(self, "Error", f"Failed to generate cover letter: {error}")

    def _open_pdf(self):
        """Open PDF in default viewer."""
        if self.job is not None and self.job.cover_letter_pdf_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.job.cover_letter_pdf_path)))

    # === Edit Field Handlers ===

    def _on_company_changed(self, value: str):
        """Handle company field change."""
        if self.job is not None and value:
            self.job.company = value
            self.title_label.setText(self.job.title)  # Refresh header
            self.company_label.setText(value)

    def _on_title_changed(self, value: str):
        """Handle title field change."""
        if self.job is not None and value:
            self.job.title = value
            self.title_label.setText(value)

    def _on_location_changed(self, value: str):
        """Handle location field change."""
        if self.job is not None:
            self.job.location = value
            self.location_label.setText(f"Location: {value or 'Not specified'}")

    def _on_link_changed(self, value: str):
        """Handle link field change."""
        if self.job is not None:
            self.job.link = value
            self.link_btn.setVisible(bool(value))

    def _on_addressee_changed(self, value: str):
        """Handle addressee field change."""
        if self.job is not None:
            self.job.addressee = value if value else None

    # === Description Handlers ===

    def _edit_description(self):
        """Edit/add full job description in a dialog."""
        if self.job is None:
            return
        desc = self.job.full_description or ""
        title = "Edit Full Job Description" if desc else "Add Full Job Description"
        dialog = TextEditDialog(title, desc, readonly=False, parent=self)
        if dialog.exec():
            new_desc = dialog.get_text()
            self.job.full_description = new_desc
            # Clear cover letter topics so they'll be regenerated
            if hasattr(self.job, 'cover_letter_topics'):
                self.job.cover_letter_topics = []
            self.refresh()

    # === Questions Handlers ===

    def _add_questions(self):
        """Add application questions via dialog."""
        if self.job is None:
            return
        dialog = AddQuestionsDialog(self)
        if dialog.exec():
            questions = dialog.get_questions()
            for q in questions:
                self.job.add_question(q)
            self.refresh()
            QMessageBox.information(self, "Success", f"Added {len(questions)} question(s)")

    def _generate_answers(self):
        """Generate AI answers for unanswered questions."""
        if self.job is None:
            return

        # Find unanswered questions
        unanswered = [q for q in self.job.questions if not q.get('answer')]
        if not unanswered:
            # All have answers, ask if they want to regenerate
            reply = QMessageBox.question(
                self, "Regenerate Answers",
                "All questions have answers. Regenerate all?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                unanswered = self.job.questions
            else:
                return

        # Check for user background
        user_background = self.user.comprehensive_summary or combined_documents_as_string(
            self.user.combined_source_documents
        )
        if not user_background:
            QMessageBox.warning(
                self, "Missing Profile",
                "Cannot generate answers: no source documents configured.\n"
                "Add your resume/CV in User Info first."
            )
            return

        # Disable button and show progress
        self.generate_answers_btn.setEnabled(False)
        self.questions_progress.show()
        self.questions_progress.setText(f"Generating answers for {len(unanswered)} questions...")

        job_description = self.job.full_description or self.job.description or ""

        def do_generate():
            return generate_answers_batch(
                questions=[q['question'] for q in unanswered],
                job_title=self.job.title,
                company=self.job.company,
                job_description=job_description,
                user_background=user_background
            )

        self.current_worker = Worker(do_generate)
        self.current_worker.finished.connect(self._on_answers_generated)
        self.current_worker.error.connect(self._on_answers_error)
        self.current_worker.start()

    def _on_answers_generated(self, results):
        """Handle answer generation completion."""
        self.generate_answers_btn.setEnabled(True)
        self.questions_progress.hide()

        if results:
            # Map results back to questions
            results_map = {r['question']: r['answer'] for r in results}
            for q in self.job.questions:
                if q['question'] in results_map and results_map[q['question']]:
                    self.job.update_question_answer(q['question'], results_map[q['question']])
            QMessageBox.information(self, "Success", f"Generated {len(results)} answer(s)")
        else:
            QMessageBox.warning(self, "Warning", "Failed to generate answers")

        self.refresh()

    def _on_answers_error(self, error: str):
        """Handle answer generation error."""
        self.generate_answers_btn.setEnabled(True)
        self.questions_progress.hide()
        QMessageBox.critical(self, "Error", f"Failed to generate answers: {error}")

    def _clear_questions(self):
        """Clear all questions after confirmation."""
        if self.job is None:
            return
        count = len(self.job.questions)
        if count == 0:
            return
        reply = QMessageBox.question(
            self, "Clear Questions",
            f"Clear all {count} question(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.job.questions = []
            self.refresh()

    # === Writing Instructions Handlers ===

    def _add_writing_instruction(self):
        """Add a job-specific writing instruction."""
        if self.job is None:
            return
        text, ok = QInputDialog.getText(
            self, "Add Instruction",
            "Enter a job-specific writing instruction:"
        )
        if ok and text.strip():
            instructions = self.job.writing_instructions or []
            instructions.append(text.strip())
            self.job.writing_instructions = instructions
            self.refresh()

    def _remove_writing_instruction(self, instruction: str):
        """Remove a job-specific writing instruction."""
        if self.job is None:
            return
        instructions = list(self.job.writing_instructions or [])
        if instruction in instructions:
            instructions.remove(instruction)
            self.job.writing_instructions = instructions
            self.refresh()

    # === Cover Letter Handlers ===

    def _edit_cover_letter(self):
        """Edit cover letter body in a dialog."""
        if self.job is None or not self.job.cover_letter_body:
            return
        dialog = TextEditDialog("Edit Cover Letter Body", self.job.cover_letter_body, readonly=False, parent=self)
        if dialog.exec():
            self.job.cover_letter_body = dialog.get_text()
            self.refresh()
            # Regenerate PDF
            self._regenerate_pdf()

    def _regenerate_pdf(self):
        """Regenerate the PDF from the current cover letter body."""
        if self.job is None or not self.job.cover_letter_body:
            return

        self.progress_label.setText("Regenerating PDF...")
        self.progress_label.show()

        service = CoverLetterService(job=self.job, user=self.user)
        self.current_worker = Worker(service.export_pdf)
        self.current_worker.finished.connect(self._on_pdf_regenerated)
        self.current_worker.error.connect(self._on_pdf_error)
        self.current_worker.start()

    def _on_pdf_regenerated(self, result):
        """Handle PDF regeneration completion."""
        self.progress_label.hide()
        if result.success:
            self.refresh()
        else:
            QMessageBox.warning(self, "Warning", f"Failed to regenerate PDF: {result.message}")

    def _on_pdf_error(self, error: str):
        """Handle PDF regeneration error."""
        self.progress_label.hide()
        QMessageBox.critical(self, "Error", f"Failed to regenerate PDF: {error}")

    # === Clipboard Handlers ===

    def _copy_cover_letter_text(self):
        """Copy cover letter text to clipboard."""
        if self.job is None or not self.job.cover_letter_body:
            return
        full_text = self.job.cover_letter_full_text(
            name_for_letter=self.user.name_with_credentials
        )
        QApplication.clipboard().setText(full_text)
        QMessageBox.information(self, "Copied", "Cover letter copied to clipboard")

    def _copy_pdf_path(self):
        """Copy PDF path to clipboard."""
        if self.job is None or not self.job.cover_letter_pdf_path:
            return
        path = str(self.job.cover_letter_pdf_path)
        QApplication.clipboard().setText(path)
        QMessageBox.information(self, "Copied", f"PDF path copied to clipboard:\n{path}")
