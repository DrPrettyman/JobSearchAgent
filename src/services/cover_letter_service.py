"""Cover letter generation service."""

from pathlib import Path
from dataclasses import dataclass

from data_handlers import Job, User
from utils import combined_documents_as_string
from services.progress import ProgressCallbackType, print_progress
from cover_letter_writer import (
    LetterWriter,
    generate_cover_letter_topics,
    generate_cover_letter_body,
)


@dataclass
class CoverLetterResult:
    """Result of cover letter generation."""
    success: bool
    message: str
    topics_generated: bool = False
    body_generated: bool = False
    pdf_path: Path | None = None


class CoverLetterService:
    """Service for generating cover letters."""

    def __init__(
        self,
        job: Job,
        user: User,
        on_progress: ProgressCallbackType = print_progress
    ):
        self.job = job
        self.user = user
        self.on_progress = on_progress

    @property
    def writing_instructions(self) -> list[str]:
        """Get writing instructions with priority: job > user > defaults."""
        instructions = []
        if self.job.writing_instructions:
            instructions.extend(self.job.writing_instructions)
        if self.user.cover_letter_writing_instructions:
            instructions.extend(self.user.cover_letter_writing_instructions)
        return list(set(instructions))

    def generate(self, force_regenerate_topics: bool = False) -> CoverLetterResult:
        """Generate a complete cover letter for a job.

        This handles the full workflow:
        1. Validate inputs (job description, user background)
        2. Generate cover letter topics (if not already present)
        3. Generate cover letter body
        4. Compile to PDF

        Args:
            force_regenerate_topics: If True, regenerate topics even if present

        Returns:
            CoverLetterResult with success status and details
        """
        # Validate job description
        job_description = self.job.full_description or self.job.description
        if not job_description:
            return CoverLetterResult(
                success=False,
                message="No job description available"
            )

        # Validate user background
        user_background = (
            self.user.comprehensive_summary
            or combined_documents_as_string(self.user.combined_source_documents)
        )
        if not user_background:
            return CoverLetterResult(
                success=False,
                message="No source documents configured"
            )

        # Warn if no comprehensive summary
        if not self.user.comprehensive_summary:
            self.on_progress(
                "Tip: Generate a comprehensive summary for better cover letters",
                "warning"
            )

        # Step 1: Generate cover letter topics
        topics_generated = False
        if not self.job.cover_letter_topics or force_regenerate_topics:
            self.on_progress("Analyzing job description...", "info")
            topics = generate_cover_letter_topics(
                job_description=job_description,
                user_background=user_background
            )
            if not topics:
                return CoverLetterResult(
                    success=False,
                    message="Failed to analyze job description"
                )
            self.job.cover_letter_topics = topics
            topics_generated = True
            self.on_progress(f"Identified {len(topics)} key topics", "success")

        # Step 2: Generate cover letter body
        self.on_progress("Generating cover letter...", "info")
        body = generate_cover_letter_body(
            job_title=self.job.title,
            company=self.job.company,
            job_description=job_description,
            user_background=user_background,
            cover_letter_topics=self.job.cover_letter_topics,
            writing_instructions=self.writing_instructions
        )

        if not body:
            return CoverLetterResult(
                success=False,
                message="Failed to generate cover letter body",
                topics_generated=topics_generated
            )

        self.job.cover_letter_body = body

        # Step 3: Compile to PDF
        self.on_progress("Compiling PDF...", "info")
        pdf_result = self.export_pdf()

        if not pdf_result.success:
            return CoverLetterResult(
                success=False,
                message=pdf_result.message,
                topics_generated=topics_generated,
                body_generated=True
            )

        return CoverLetterResult(
            success=True,
            message="Cover letter generated successfully",
            topics_generated=topics_generated,
            body_generated=True,
            pdf_path=pdf_result.pdf_path
        )

    def export_pdf(self) -> CoverLetterResult:
        """Export an existing cover letter to PDF.

        Requires job.cover_letter_body to be set.

        Returns:
            CoverLetterResult with PDF path on success
        """
        if not self.job.cover_letter_body:
            return CoverLetterResult(
                success=False,
                message="No cover letter body to export"
            )

        # Get first non-LinkedIn website for the cover letter header
        non_linkedin_sites = [s for s in self.user.websites if "linkedin.com" not in s.lower()]

        letter_writer = LetterWriter(
            company=self.job.company,
            title=self.job.title,
            cover_letter_body=self.job.cover_letter_body,
            user_name=self.user.name,
            user_email=self.user.email,
            user_linkedin_url=self.user.linkedin_url,
            user_credentials=self.user.credentials,
            user_website=non_linkedin_sites[0] if non_linkedin_sites else None,
            addressee=self.job.addressee,
        )

        pdf_path = letter_writer.save_pdf(
            output_dir=self.user.cover_letter_output_dir,
            on_progress=self.on_progress
        )

        if pdf_path is None:
            return CoverLetterResult(
                success=False,
                message="Failed to compile PDF"
            )

        self.job.set_cover_letter_pdf_path(pdf_path.resolve())

        return CoverLetterResult(
            success=True,
            message="PDF exported successfully",
            pdf_path=pdf_path
        )

    def regenerate_body_only(self) -> CoverLetterResult:
        """Regenerate just the cover letter body, keeping existing topics.

        Returns:
            CoverLetterResult with success status
        """
        if not self.job.cover_letter_topics:
            return CoverLetterResult(
                success=False,
                message="No topics available - generate full cover letter first"
            )

        job_description = self.job.full_description or self.job.description
        if not job_description:
            return CoverLetterResult(
                success=False,
                message="No job description available"
            )

        user_background = (
            self.user.comprehensive_summary
            or combined_documents_as_string(self.user.combined_source_documents)
        )
        if not user_background:
            return CoverLetterResult(
                success=False,
                message="No source documents configured"
            )

        self.on_progress("Regenerating cover letter...", "info")
        body = generate_cover_letter_body(
            job_title=self.job.title,
            company=self.job.company,
            job_description=job_description,
            user_background=user_background,
            cover_letter_topics=self.job.cover_letter_topics,
            writing_instructions=self.writing_instructions
        )

        if not body:
            return CoverLetterResult(
                success=False,
                message="Failed to generate cover letter body"
            )

        self.job.cover_letter_body = body

        # Also regenerate PDF
        return self.export_pdf()
