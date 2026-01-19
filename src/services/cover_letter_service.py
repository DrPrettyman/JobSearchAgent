"""Cover letter generation service."""

from pathlib import Path
from dataclasses import dataclass

from data_handlers import Job, User
from utils import combined_documents_as_string
from services.progress import ProgressCallbackType, print_progress


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

    def __init__(self, on_progress: ProgressCallbackType = print_progress):
        self.on_progress = on_progress

    def generate(
        self,
        job: Job,
        user: User,
        force_regenerate_topics: bool = False,
        writing_instructions: list[str] | None = None
    ) -> CoverLetterResult:
        """Generate a complete cover letter for a job.

        This handles the full workflow:
        1. Validate inputs (job description, user background)
        2. Generate cover letter topics (if not already present)
        3. Generate cover letter body
        4. Compile to PDF

        Args:
            job: The job to generate a cover letter for
            user: The user whose background to use
            force_regenerate_topics: If True, regenerate topics even if present
            writing_instructions: Custom instructions for writing style (uses defaults if None)

        Returns:
            CoverLetterResult with success status and details
        """
        # Validate job description
        job_description = job.full_description or job.description
        if not job_description:
            return CoverLetterResult(
                success=False,
                message="No job description available"
            )

        # Validate user background
        user_background = (
            user.comprehensive_summary
            or combined_documents_as_string(user.combined_source_documents)
        )
        if not user_background:
            return CoverLetterResult(
                success=False,
                message="No source documents configured"
            )

        # Warn if no comprehensive summary
        if not user.comprehensive_summary:
            self.on_progress(
                "Tip: Generate a comprehensive summary for better cover letters",
                "warning"
            )

        # Lazy import to avoid circular dependency
        from cover_letter_writer import (
            LetterWriter,
            generate_cover_letter_topics,
            generate_cover_letter_body,
            DEFAULT_WRITING_INSTRUCTIONS,
        )

        # Use user's custom instructions, or default if none provided
        if writing_instructions is None:
            writing_instructions = user.cover_letter_writing_instructions or DEFAULT_WRITING_INSTRUCTIONS

        # Step 1: Generate cover letter topics
        topics_generated = False
        if not job.cover_letter_topics or force_regenerate_topics:
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
            job.cover_letter_topics = topics
            topics_generated = True
            self.on_progress(f"Identified {len(topics)} key topics", "success")

        # Step 2: Generate cover letter body
        self.on_progress("Generating cover letter...", "info")
        body = generate_cover_letter_body(
            job_title=job.title,
            company=job.company,
            job_description=job_description,
            user_background=user_background,
            cover_letter_topics=job.cover_letter_topics,
            writing_instructions=writing_instructions
        )

        if not body:
            return CoverLetterResult(
                success=False,
                message="Failed to generate cover letter body",
                topics_generated=topics_generated
            )

        job.cover_letter_body = body

        # Step 3: Compile to PDF
        self.on_progress("Compiling PDF...", "info")
        pdf_result = self.export_pdf(job, user)

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

    def export_pdf(self, job: Job, user: User) -> CoverLetterResult:
        """Export an existing cover letter to PDF.

        Requires job.cover_letter_body to be set.

        Args:
            job: The job with cover letter body
            user: The user for letterhead info

        Returns:
            CoverLetterResult with PDF path on success
        """
        if not job.cover_letter_body:
            return CoverLetterResult(
                success=False,
                message="No cover letter body to export"
            )

        # Lazy import to avoid circular dependency
        from cover_letter_writer import LetterWriter

        # Get first non-LinkedIn website for the cover letter header
        non_linkedin_sites = [s for s in user.websites if "linkedin.com" not in s.lower()]

        letter_writer = LetterWriter(
            company=job.company,
            title=job.title,
            cover_letter_body=job.cover_letter_body,
            user_name=user.name,
            user_email=user.email,
            user_linkedin_url=user.linkedin_url,
            user_credentials=user.credentials,
            user_website=non_linkedin_sites[0] if non_linkedin_sites else None,
            addressee=job.addressee,
        )

        pdf_path = letter_writer.save_pdf(
            output_dir=user.cover_letter_output_dir,
            on_progress=self.on_progress
        )

        if pdf_path is None:
            return CoverLetterResult(
                success=False,
                message="Failed to compile PDF"
            )

        job.set_cover_letter_pdf_path(pdf_path.resolve())

        return CoverLetterResult(
            success=True,
            message="PDF exported successfully",
            pdf_path=pdf_path
        )

    def regenerate_body_only(
        self,
        job: Job,
        user: User,
        writing_instructions: list[str] | None = None
    ) -> CoverLetterResult:
        """Regenerate just the cover letter body, keeping existing topics.

        Args:
            job: The job (must have cover_letter_topics set)
            user: The user whose background to use
            writing_instructions: Custom instructions for writing style (uses defaults if None)

        Returns:
            CoverLetterResult with success status
        """
        if not job.cover_letter_topics:
            return CoverLetterResult(
                success=False,
                message="No topics available - generate full cover letter first"
            )

        job_description = job.full_description or job.description
        if not job_description:
            return CoverLetterResult(
                success=False,
                message="No job description available"
            )

        user_background = (
            user.comprehensive_summary
            or combined_documents_as_string(user.combined_source_documents)
        )
        if not user_background:
            return CoverLetterResult(
                success=False,
                message="No source documents configured"
            )

        self.on_progress("Regenerating cover letter...", "info")
        # Lazy import to avoid circular dependency
        from cover_letter_writer import generate_cover_letter_body, DEFAULT_WRITING_INSTRUCTIONS

        # Use user's custom instructions, or default if none provided
        if writing_instructions is None:
            writing_instructions = user.cover_letter_writing_instructions or DEFAULT_WRITING_INSTRUCTIONS

        body = generate_cover_letter_body(
            job_title=job.title,
            company=job.company,
            job_description=job_description,
            user_background=user_background,
            cover_letter_topics=job.cover_letter_topics,
            writing_instructions=writing_instructions
        )

        if not body:
            return CoverLetterResult(
                success=False,
                message="Failed to generate cover letter body"
            )

        job.cover_letter_body = body

        # Also regenerate PDF
        return self.export_pdf(job, user)
