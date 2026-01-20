"""CLI menu functions for JobSearch application."""

import os
import platform
import shutil
import subprocess
import time
import urllib.parse
import webbrowser
from pathlib import Path
from datetime import datetime


def get_platform() -> str:
    """Return normalized platform name: 'macos', 'windows', or 'linux'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    return "linux"


def open_file(path: str) -> bool:
    """Open a file with the system's default application. Returns True on success."""
    try:
        plat = get_platform()
        if plat == "macos":
            subprocess.run(["open", path], check=True)
        elif plat == "windows":
            os.startfile(path)
        else:  # Linux
            subprocess.run(["xdg-open", path], check=True)
        return True
    except Exception:
        return False


def copy_text_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success."""
    try:
        plat = get_platform()
        if plat == "macos":
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
        elif plat == "windows":
            subprocess.run(["clip"], input=text.encode(), check=True, shell=True)
        else:  # Linux - try xclip, fall back to xsel
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode(),
                    check=True
                )
            except FileNotFoundError:
                subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode(),
                    check=True
                )
        return True
    except Exception:
        return False


def copy_pdf_to_clipboard(path: str) -> tuple[bool, str]:
    """Copy PDF file to clipboard. Returns (success, message)."""
    plat = get_platform()
    if plat == "macos":
        try:
            script = f'set the clipboard to (read (POSIX file "{path}") as «class PDF »)'
            subprocess.run(["osascript", "-e", script], check=True)
            return True, "PDF copied to clipboard"
        except Exception:
            return False, "Failed to copy PDF to clipboard"
    elif plat == "windows":
        # Windows doesn't have a simple way to copy PDF as file to clipboard from CLI
        # Copy the file path instead
        try:
            subprocess.run(["clip"], input=path.encode(), check=True, shell=True)
            return True, "PDF file path copied to clipboard (use Ctrl+V to paste path)"
        except Exception:
            return False, "Failed to copy to clipboard"
    else:  # Linux
        # Linux also lacks simple PDF-to-clipboard; copy path instead
        try:
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=path.encode(),
                    check=True
                )
            except FileNotFoundError:
                subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=path.encode(),
                    check=True
                )
            return True, "PDF file path copied to clipboard"
        except Exception:
            return False, "Failed to copy to clipboard (install xclip or xsel)"

from InquirerPy import inquirer
from InquirerPy.validator import PathValidator

from data_handlers import User, Job, JobStatus
from cli_utils import (
    Colors,
    DEFAULT_WIDTH,
    ASCII_ART_JOBSEARCH,
    clear_screen,
    print_header,
    print_section,
    print_field,
    print_list,
    print_numbered_list,
    print_inline_list,
    print_status_summary,
    print_box,
    print_thick_line,
    text_to_lines,
    hyperlink,
    display_job_card,
    display_job_detail
)
from utils import (
    combined_documents_as_string,
    summarize_source_documents,
    combine_documents,
)
from search_jobs import JobSearcher
from services import CoverLetterService, UserProfileService
from question_answerer import generate_answers_batch

# Ordered by precedence (most prestigious first)
CREDENTIAL_OPTIONS = [
    "PhD", "MD", "JD", "EdD", "DBA", "MBA", "MS", "MA",
    "MEng", "MFA", "MPH", "CPA", "CFA", "PMP", "PE",
]


class JobOptions:
    def __init__(self, user: User, job_id: str):
        self.user: User = user
        self.job: Job = user.job_handler[job_id]

    def export_pdf_cover_letter(self):
        """Export cover letter to PDF using the service."""
        service = CoverLetterService(
            job=self.job,
            user=self.user,
            on_progress=lambda msg, level: print(
                f"{Colors.RED if level == 'error' else Colors.CYAN}{msg}{Colors.RESET}"
            )
        )
        result = service.export_pdf()
        if not result.success:
            print(f"{Colors.RED}{result.message}{Colors.RESET}\n")

    def generate_cover_letter_for_job(self):
        """Generate cover letter content for a job."""
        service = CoverLetterService(
            job=self.job,
            user=self.user,
            on_progress=lambda msg, level: print(
                f"{Colors.GREEN if level == 'success' else Colors.YELLOW if level == 'warning' else Colors.CYAN}{msg}{Colors.RESET}"
            )
        )

        result = service.generate()

        if result.success:
            print(f"{Colors.GREEN}✓ Cover letter generated!{Colors.RESET}\n")
        else:
            print(f"{Colors.RED}{result.message}{Colors.RESET}\n")

    def add_questions(self):
        """Allow user to paste application questions."""
        clear_screen()
        print_header(f"Add Questions: {self.job.title} at {self.job.company}")

        if self.job.questions:
            print()
            print_numbered_list("Current questions", [q['question'] for q in self.job.questions])
            print()

        print(f"{Colors.YELLOW}Paste your application questions below (one per line).{Colors.RESET}")
        print(f"{Colors.DIM}Type 'DONE' on a new line when finished, or 'CANCEL' to abort.{Colors.RESET}\n")

        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "DONE":
                    break
                if line.strip().upper() == "CANCEL":
                    print(f"\n{Colors.YELLOW}Cancelled.{Colors.RESET}\n")
                    input("Press Enter to continue...")
                    return
                lines.append(line)
            except EOFError:
                break

        # Parse questions (non-empty lines)
        new_questions = [line.strip() for line in lines if line.strip()]

        if not new_questions:
            print(f"\n{Colors.YELLOW}No questions entered.{Colors.RESET}\n")
            input("Press Enter to continue...")
            return

        # Add new questions (without answers)
        for q in new_questions:
            self.job.add_question(q)
        print(f"\n{Colors.GREEN}✓ Added {len(new_questions)} questions{Colors.RESET}\n")
        input("Press Enter to continue...")

    def generate_question_answers(self):
        """Generate AI answers for unanswered questions."""
        if not self.job.questions:
            print(f"\n{Colors.YELLOW}No questions to answer. Add questions first.{Colors.RESET}\n")
            input("Press Enter to continue...")
            return

        # Find questions without answers
        unanswered = [q for q in self.job.questions if not q.get("answer")]

        if not unanswered:
            print(f"\n{Colors.YELLOW}All questions already have answers.{Colors.RESET}")
            regenerate = inquirer.confirm(
                message="Regenerate all answers?",
                default=False
            ).execute()
            if regenerate:
                unanswered = self.job.questions
            else:
                return

        # Get user background
        user_background = self.user.comprehensive_summary or combined_documents_as_string(self.user.combined_source_documents)

        if not user_background:
            print(f"\n{Colors.RED}Cannot generate: no source documents configured.{Colors.RESET}")
            print(f"{Colors.DIM}Add your resume/CV in User Info first.{Colors.RESET}\n")
            input("Press Enter to continue...")
            return

        job_description = self.job.full_description or self.job.description

        print(f"\n{Colors.CYAN}Generating answers for {len(unanswered)} questions...{Colors.RESET}")

        # Use batch generation for efficiency
        questions_text = [q["question"] for q in unanswered]
        results = generate_answers_batch(
            questions=questions_text,
            job_title=self.job.title,
            company=self.job.company,
            job_description=job_description,
            user_background=user_background
        )

        if results:
            # Match results back to questions
            results_map = {r["question"]: r["answer"] for r in results}
            for q in self.job.questions:
                if q["question"] in results_map and results_map[q["question"]]:
                    self.job.update_question_answer(q["question"], results_map[q["question"]])

            print(f"{Colors.GREEN}✓ Generated {len(results)} answers!{Colors.RESET}\n")
        else:
            print(f"{Colors.RED}Failed to generate answers.{Colors.RESET}\n")

        input("Press Enter to continue...")

    def view_questions(self):
        """View all questions and answers for this job."""
        clear_screen()
        print_header(f"Questions: {self.job.title} at {self.job.company}")

        if not self.job.questions:
            print(f"  {Colors.DIM}No questions added yet.{Colors.RESET}\n")
            input("Press Enter to continue...")
            return

        for i, qa in enumerate(self.job.questions, 1):
            # Wrap question text
            q_lines = text_to_lines(qa['question'], width=DEFAULT_WIDTH - 6)
            print(f"\n{Colors.BOLD}{Colors.CYAN}Q{i}: {q_lines[0]}{Colors.RESET}")
            for q_line in q_lines[1:]:
                print(f"    {Colors.BOLD}{Colors.CYAN}{q_line}{Colors.RESET}")

            if qa.get("answer"):
                print(f"{Colors.DIM}{'─' * 40}{Colors.RESET}")
                # Word wrap the answer
                for line in text_to_lines(qa["answer"], width=DEFAULT_WIDTH - 4):
                    print(f"  {line}")
            else:
                print(f"  {Colors.YELLOW}(no answer generated){Colors.RESET}")

        print()
        print_thick_line()
        input("\nPress Enter to continue...")

    def clear_questions(self):
        """Clear all questions for this job."""
        if not self.job.questions:
            print(f"\n{Colors.YELLOW}No questions to clear.{Colors.RESET}\n")
            return

        confirm = inquirer.confirm(
            message=f"Clear all {len(self.job.questions)} questions?",
            default=False
        ).execute()

        if confirm:
            self.job.questions = []
            print(f"\n{Colors.GREEN}✓ Questions cleared.{Colors.RESET}\n")

    def configure_job_writing_instructions(self):
        """Configure job-specific cover letter writing instructions."""
        while True:
            clear_screen()
            print_header(f"Writing Style: {self.job.title}")
            
            general_instructions = self.user.cover_letter_writing_instructions
            print_numbered_list("General writing instructions", general_instructions)
            print()

            job_instructions = self.job.writing_instructions
            print_numbered_list("Specific instructions for this job", job_instructions)
            print()

            choices = [{"name": "Add job-specific instruction", "value": "add"}]
            if job_instructions:
                choices.append({"name": "Remove job-specific instruction", "value": "remove"})
            choices.append({"name": "Done", "value": "done"})

            action = inquirer.select(message="Action:", choices=choices).execute()

            if action == "done":
                break
            elif action == "add":
                instruction = inquirer.text(
                    message="Enter instruction:",
                    validate=lambda x: len(x.strip()) > 0
                ).execute()
                if instruction:
                    job_instructions.append(instruction.strip())
                    self.job.writing_instructions = job_instructions
            elif action == "remove":
                to_remove = inquirer.select(
                    message="Select instruction to remove:",
                    choices=[
                        {"name": f"{i}. {inst[:60]}{'...' if len(inst) > 60 else ''}", "value": i-1}
                        for i, inst in enumerate(job_instructions, 1)
                    ] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove is not None:
                    job_instructions.pop(to_remove)
                    self.job.writing_instructions = job_instructions

    def edit_job_details(self):
        """Edit basic job details (company, title, location, link, addressee)."""
        while True:
            clear_screen()
            print_header(f"Edit Job Details")

            print_section("Current Details")
            print_field("Company", self.job.company)
            print_field("Title", self.job.title)
            print_field("Location", self.job.location)
            print_field("Link", self.job.link)
            print_field("Hiring Manager", self.job.addressee)
            print()

            action = inquirer.select(
                message="What would you like to edit?",
                choices=[
                    {"name": "Company", "value": "company"},
                    {"name": "Title", "value": "title"},
                    {"name": "Location", "value": "location"},
                    {"name": "Link", "value": "link"},
                    {"name": "Hiring Manager", "value": "addressee"},
                    {"name": "← Done", "value": "done"},
                ],
            ).execute()

            if action == "done":
                break
            elif action == "company":
                new_value = inquirer.text(
                    message="Company name:",
                    default=self.job.company,
                ).execute()
                if new_value:
                    self.job.company = new_value
            elif action == "title":
                new_value = inquirer.text(
                    message="Job title:",
                    default=self.job.title,
                ).execute()
                if new_value:
                    self.job.title = new_value
            elif action == "location":
                new_value = inquirer.text(
                    message="Location:",
                    default=self.job.location or "",
                ).execute()
                self.job.location = new_value
            elif action == "link":
                new_value = inquirer.text(
                    message="Job posting URL:",
                    default=self.job.link or "",
                ).execute()
                self.job.link = new_value
            elif action == "addressee":
                new_value = inquirer.text(
                    message="Hiring manager name (leave blank if unknown):",
                    default=self.job.addressee or "",
                ).execute()
                self.job.addressee = new_value if new_value else None

    
    def edit_job_description(self):
        """Allow user to paste/edit the job description."""
        clear_screen()
        print_header(f"Edit Description: {self.job.title} at {self.job.company}")

        if self.job.full_description:
            print(f"\n{Colors.CYAN}Current description:{Colors.RESET}")
            preview = self.job.full_description[:500]
            if len(self.job.full_description) > 500:
                preview += "..."
            for line in text_to_lines(preview, width=DEFAULT_WIDTH - 2):
                print(f"{Colors.DIM}{line}{Colors.RESET}")
            print()

        print(f"{Colors.YELLOW}Paste the job description below.{Colors.RESET}")
        print(f"{Colors.DIM}Type 'DONE' on a new line when finished, or 'CANCEL' to abort.{Colors.RESET}\n")

        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "DONE":
                    break
                if line.strip().upper() == "CANCEL":
                    print(f"\n{Colors.YELLOW}Cancelled.{Colors.RESET}\n")
                    input("Press Enter to continue...")
                    return
                lines.append(line)
            except EOFError:
                break

        new_description = "\n".join(lines).strip()

        if not new_description:
            print(f"\n{Colors.YELLOW}No description entered.{Colors.RESET}\n")
            input("Press Enter to continue...")
            return

        self.job.full_description = new_description
        # Clear cover letter topics so they'll be regenerated with new description
        if self.job.cover_letter_topics:
            self.job.cover_letter_topics = []
        print(f"\n{Colors.GREEN}✓ Job description updated ({len(new_description)} characters){Colors.RESET}\n")
        input("Press Enter to continue...")

    def menu(self):
        """View and manage a single job."""
        while True:
            clear_screen()
            display_job_detail(self.job)

            choices = []
            # Status transition options based on current status
            if self.job.status == JobStatus.PENDING:
                choices.append({"name": "▶ Mark as in progress", "value": "in_progress"})
                choices.append({"name": "✓ Mark as applied", "value": "apply"})
                choices.append({"name": "✗ Discard job", "value": "discard"})
            elif self.job.status == JobStatus.IN_PROGRESS:
                choices.append({"name": "✓ Mark as applied", "value": "apply"})
                choices.append({"name": "○ Mark as pending", "value": "pending"})
                choices.append({"name": "✗ Discard job", "value": "discard"})
            elif self.job.status == JobStatus.APPLIED:
                choices.append({"name": "○ Mark as not applied", "value": "unapply"})
                choices.append({"name": "✗ Discard job", "value": "discard"})
            elif self.job.status == JobStatus.DISCARDED:
                choices.append({"name": "○ Restore job", "value": "restore"})

            if self.job.link:
                choices.append({"name": "🔗 Open job link", "value": "open_link"})
            choices.append({"name": "🔍 Google this job", "value": "google_job"})

            choices.append({"name": "✏️ Edit job details", "value": "edit_details"})

            # Option to add/edit job description
            if self.job.full_description:
                choices.append({"name": "👁️ View full description", "value": "view_description"})
                choices.append({"name": "📝 Edit job description", "value": "edit_description"})
            else:
                choices.append({"name": "📝 Add job description", "value": "edit_description"})

            if self.job.cover_letter_body:
                choices.append({"name": "🔄 Regenerate cover letter", "value": "cover_letter_generate"})
                choices.append({"name": "📄 Copy plain text cover letter to clipboard", "value": "cover_letter_text_clipboard"})
            else:
                choices.append({"name": "📄 Generate cover letter", "value": "cover_letter_generate"})

            # Questions section
            if self.job.questions:
                unanswered = sum(1 for q in self.job.questions if not q.get("answer"))
                choices.append({"name": f"❓ View questions ({len(self.job.questions)})", "value": "view_questions"})
                choices.append({"name": "❓ Add more questions", "value": "add_questions"})
                if unanswered:
                    choices.append({"name": f"✨ Generate answers ({unanswered} unanswered)", "value": "generate_answers"})
                else:
                    choices.append({"name": "🔄 Regenerate answers", "value": "generate_answers"})
                choices.append({"name": "🗑️ Clear all questions", "value": "clear_questions"})
            else:
                choices.append({"name": "❓ Add application questions", "value": "add_questions"})
            
            if self.job.cover_letter_pdf_path is not None:
                choices.append({"name": "📄 Open PDF cover letter", "value": "cover_letter_open"})
                choices.append({"name": "📄 Copy PDF cover letter to clipboard", "value": "cover_letter_pdf_clipboard"})
            else:
                if self.job.cover_letter_body:
                    choices.append({"name": "📄 Retry PDF cover letter export", "value": "cover_letter_pdf_export"})

            # Writing style option
            if self.job.writing_instructions:
                choices.append({"name": "✏️ Edit writing style (custom)", "value": "writing_instructions"})
            else:
                choices.append({"name": "✏️ Set custom writing style", "value": "writing_instructions"})

            choices.append({"name": "← Back to jobs list", "value": "back"})

            print()
            print_thick_line()
            print()

            action = inquirer.select(
                message="What would you like to do?",
                choices=choices,
            ).execute()

            if action == "back":
                break
            elif action == "apply":
                self.job.status = JobStatus.APPLIED
                print(f"\n{Colors.GREEN}✓ Marked as applied!{Colors.RESET}\n")
                time.sleep(1)
                return
            elif action == "unapply":
                self.job.status = JobStatus.IN_PROGRESS
                print(f"\n{Colors.YELLOW}○ Marked as not applied.{Colors.RESET}\n")
                time.sleep(1)
                return
            elif action == "in_progress":
                self.job.status = JobStatus.IN_PROGRESS
                print(f"\n{Colors.CYAN}▶ Marked as in progress.{Colors.RESET}\n")
                time.sleep(1)
                return
            elif action == "pending":
                self.job.status = JobStatus.PENDING
                print(f"\n{Colors.YELLOW}○ Marked as pending.{Colors.RESET}\n")
                time.sleep(1)
                return
            elif action == "discard":
                self.user.discard_job(job_id=self.job.id)
                print(f"\n{Colors.RED}✗ Job discarded.{Colors.RESET}\n")
                time.sleep(1)
                return
            elif action == "restore":
                self.user.restore_job(job_id=self.job.id)
                print(f"\n{Colors.YELLOW}○ Job restored.{Colors.RESET}\n")
                time.sleep(1)
                return
            elif action == "open_link":
                webbrowser.open(self.job.link)
                print(f"\n{Colors.DIM}Opening in browser...{Colors.RESET}\n")
            elif action == "google_job":
                query = urllib.parse.quote(f"careers {self.job.company} {self.job.title}")
                webbrowser.open(f"https://www.google.com/search?q={query}")
                print(f"\n{Colors.DIM}Opening Google search...{Colors.RESET}\n")
            elif action == "edit_details":
                self.edit_job_details()
            elif action == "view_description":
                clear_screen()
                print()
                print_header("Job Description")
                print(self.job.full_description)
                print()
                print_thick_line()
                input("Press Enter to continue...")
            elif action == "edit_description":
                self.edit_job_description()
            elif action == "cover_letter_generate":
                self.generate_cover_letter_for_job()
            elif action == "cover_letter_open":
                if open_file(str(self.job.cover_letter_pdf_path)):
                    print(f"\n{Colors.DIM}Opening PDF...{Colors.RESET}\n")
                else:
                    print(f"\n{Colors.RED}Could not open PDF. File: {self.job.cover_letter_pdf_path}{Colors.RESET}\n")
            elif action == "cover_letter_text_clipboard":
                letter_text = self.job.cover_letter_full_text(name_for_letter=self.user.name_with_credentials)
                if copy_text_to_clipboard(letter_text):
                    print(f"\n{Colors.GREEN}✓ Cover letter copied to clipboard{Colors.RESET}\n")
                else:
                    print(f"\n{Colors.RED}Could not copy to clipboard{Colors.RESET}\n")
            elif action == "cover_letter_pdf_clipboard":
                success, message = copy_pdf_to_clipboard(str(self.job.cover_letter_pdf_path))
                if success:
                    print(f"\n{Colors.GREEN}✓ {message}{Colors.RESET}\n")
                else:
                    print(f"\n{Colors.RED}{message}{Colors.RESET}\n")
            elif action == "cover_letter_pdf_export":
                self.export_pdf_cover_letter()
            elif action == "add_questions":
                self.add_questions()
            elif action == "view_questions":
                self.view_questions()
            elif action == "generate_answers":
                self.generate_question_answers()
            elif action == "clear_questions":
                self.clear_questions()
            elif action == "writing_instructions":
                self.configure_job_writing_instructions()

class UserOptions:
    """Menu for viewing and editing user information."""

    def __init__(self, user: User):
        self.user = user
        self._job_title_suggestions = []
        self._job_location_suggestions = []
        
        self._job_searcher = None
        
    @property
    def job_searcher(self):
        if self._job_searcher is None:
            self._job_searcher = JobSearcher(user=self.user)
        return self._job_searcher
        
    def first_time_setup(self):
        """Guided setup flow for first-time users."""
        clear_screen()
        print(f"{Colors.CYAN}{ASCII_ART_JOBSEARCH}{Colors.RESET}")
        print(f"  {Colors.DIM}Let's set up your profile to find the perfect job.{Colors.RESET}\n")

        # Step 1: Basic info
        print_section("Step 1: Basic Information")
        self.configure_name()
        self.configure_email()
        self.configure_credentials()

        # Step 2: Online presence
        print_section("Step 2: Online Presence")
        self.configure_websites()

        # Step 3: Source documents
        print_section("Step 3: Source Documents (CV/Resume)")
        print(f"  {Colors.DIM}Add your CV, resume, or other documents that describe your background.{Colors.RESET}\n")
        self.configure_source_documents()

        # Step 4: Job preferences
        print_section("Step 4: Job Preferences")

        # Offer AI suggestions if we have documents
        if self.user.source_document_paths or self.user.online_presence:
            use_ai = inquirer.confirm(
                message="Would you like AI to suggest job titles and locations from your documents?",
                default=True
            ).execute()
            if use_ai:
                self.create_new_job_title_and_location_suggestions()

        self.configure_job_titles()
        self.configure_job_locations()

        # Step 5: Generate comprehensive summary
        has_content = self.user.source_document_paths or self.user.online_presence
        if has_content:
            print_section("Step 5: Generate Summary")
            print(f"  {Colors.DIM}A comprehensive summary improves cover letter quality.{Colors.RESET}\n")
            generate = inquirer.confirm(
                message="Generate comprehensive summary now?",
                default=True
            ).execute()
            if generate:
                self.generate_comprehensive_summary()

        # Step 6: Generate search queries
        if self.user.desired_job_titles and self.user.desired_job_locations:
            print_section("Step 6: Search Queries")
            print(f"  {Colors.DIM}Search queries help find relevant job postings.{Colors.RESET}\n")
            generate = inquirer.confirm(
                message="Generate search queries now?",
                default=True
            ).execute()
            if generate:
                self.create_search_queries()

        print_header("Setup Complete")
        print(f"  {Colors.GREEN}✓ Your profile is ready!{Colors.RESET}")
        print(f"  {Colors.DIM}You can now search for jobs from the main menu.{Colors.RESET}\n")

    def display_user_info(self):
        """Display user information in a formatted view."""
        print_header("User Profile")

        # Basic Info
        _not_set = f"{Colors.RED}Not set{Colors.RESET}"
        print_section("Basic Information")
        print_field("Name", self.user.name_with_credentials if self.user.name else _not_set)
        print_field("Email", self.user.email if self.user.email else _not_set)
        print_field("LinkedIn", self.user.linkedin_url if self.user.linkedin_url else _not_set)
        
        print_inline_list("Desired Job Titles", self.user.desired_job_titles)
        print_inline_list("Desired Job Locations", self.user.desired_job_locations)

        # Comprehensive Summary field
        if self.user.comprehensive_summary:
            word_count = len(self.user.comprehensive_summary.split())
            generated_at = self.user.comprehensive_summary_generated_at
            if generated_at:
                try:
                    dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                    readable_time = dt.strftime("%b %d, %Y at %I:%M %p")
                except ValueError:
                    readable_time = generated_at
                summary_value = f"{word_count} words, generated {readable_time}"
            else:
                summary_value = f"{word_count} words"
        else:
            summary_value = f"{Colors.RED}Not generated{Colors.RESET}"
        print_field("Comprehensive Summary", summary_value)

        print()

        # Information sources
        print_section("Information Sources")
        for path in self.user.source_document_paths:
            print(f"  {Colors.GREEN}•{Colors.RESET} {path}")
        for entry in self.user.online_presence:
            site = entry.get("site", "Unknown")
            time_fetched = entry.get("time_fetched", "")
            try:
                dt = datetime.fromisoformat(time_fetched.replace("Z", "+00:00"))
                readable_time = dt.strftime("%b %d, %Y at %I:%M %p")
            except ValueError:
                readable_time = time_fetched
            fetch_success = entry.get("fetch_success")
            if fetch_success:
                _content_len = len(entry.get("content", ""))
                fetched_summary = f"Fetched {readable_time} ({_content_len} chars)"
            else:
                fetched_summary = f"Unable to fetch (attempted {readable_time})"
            print(f"  {Colors.GREEN}•{Colors.RESET} {hyperlink(site)} {Colors.DIM}{fetched_summary}{Colors.RESET}")
        other_websites = [s for s in self.user.websites if s not in self.user.all_online_presence_sites]
        for site in other_websites:
            print(f"  {Colors.GREEN}•{Colors.RESET} {hyperlink(site)} {Colors.DIM}Not fetched{Colors.RESET}")
            
        if self.user.source_document_summary:
            print()
            print_box("Document Summary", self.user.source_document_summary)
        if self.user.online_presence_summary:
            print()
            print_box("Online Summary", self.user.online_presence_summary)
        print()

    def configure_name(self):
        """Configure user's name."""
        clear_screen()
        print_header("Name")
        if self.user.name:
            print(f"  {Colors.DIM}Current: {self.user.name}{Colors.RESET}\n")
        else:
            print(f"  {Colors.DIM}Not set{Colors.RESET}\n")

        self.user.name = inquirer.text(
            message="Your name:",
            default=self.user.name,
        ).execute()

    def configure_email(self):
        """Configure user's email."""
        clear_screen()
        print_header("Email")
        if self.user.email:
            print(f"  {Colors.DIM}Current: {self.user.email}{Colors.RESET}\n")
        else:
            print(f"  {Colors.DIM}Not set{Colors.RESET}\n")

        self.user.email = inquirer.text(
            message="Your email:",
            default=self.user.email,
        ).execute()

    def configure_credentials(self):
        """Configure user's credentials/titles."""
        clear_screen()
        print_header("Credentials")
        current = self.user.credentials
        print_inline_list("Current", current, quote=False)
        print()

        choices = [
            {"name": cred, "value": cred, "enabled": cred in current}
            for cred in CREDENTIAL_OPTIONS
        ]
        selected = inquirer.checkbox(
            message="Select your credentials (in order of precedence):",
            choices=choices,
        ).execute()
        self.user.credentials = selected

    def configure_websites(self):
        """Configure personal websites/portfolios."""
        websites_before = set(self.user.websites)
        while True:
            clear_screen()
            print_header("Websites")
            sites = self.user.websites
            print_list("Configured websites", sites)
            print()

            choices = [{"name": "Add a website", "value": "add"}]
            if sites:
                choices.append({"name": "Remove a website", "value": "remove"})
            choices.append({"name": "← Done", "value": "done"})

            action = inquirer.select(message="Action:", choices=choices).execute()

            if action == "done":
                break
            elif action == "add":
                url = inquirer.text(message="Enter website URL:").execute()
                if url:
                    self.user.add_website(url)
            elif action == "remove":
                to_remove = inquirer.select(
                    message="Select website to remove:",
                    choices=[{"name": s, "value": s} for s in sites] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove:
                    self.user.remove_website(to_remove)


        websites_after = set(self.user.websites)

        if websites_before != websites_after:
            self.refresh_online_presence()

    def configure_job_titles(self):
        """Configure desired job titles."""
        while True:
            clear_screen()
            print_header("Desired Job Titles")
            titles = self.user.desired_job_titles
            print_list("Current titles", titles)
            print()
                
            if self._job_title_suggestions:
                print_inline_list("Suggested Job Titles", self._job_title_suggestions)
                print()
                
            choices = [
                {"name": "Add a title manually", "value": "add"},
                {"name": "Add a title from AI suggestions", "value": "use_suggestions"},
                {"name": "Generate more suggestions", "value": "generate_suggestions"}
            ]
            if titles:
                choices.append({"name": "Remove a title", "value": "remove"})
            if self._job_title_suggestions:
                choices.append({"name": "Clear AI suggestions and re-generate", "value": "regenerate_suggestions"})
            choices.append({"name": "← Done", "value": "done"})

            action = inquirer.select(message="Action:", choices=choices).execute()

            if action == "done":
                break
            elif action == "add":
                new_title = inquirer.text(message="Enter job title:").execute()
                if new_title:
                    self.user.add_desired_job_title(new_title)
            elif action == "use_suggestions":
                for _ in range(3):
                    if not self._job_title_suggestions:
                        self.create_new_job_title_and_location_suggestions()
                if not self._job_title_suggestions:
                    print(f"{Colors.RED}Could not generate suggestions{Colors.RESET}")
                if self._job_title_suggestions:
                    choices = [
                        {"name": s, "value": s, "enabled": False}
                        for s in self._job_title_suggestions
                    ]
                    selected = inquirer.checkbox(
                        message="Select titles to add:",
                        choices=choices,
                    ).execute()
                    for title in selected:
                        self.user.add_desired_job_title(title)
                        self._job_title_suggestions.remove(title)
            elif action == "generate_suggestions":
                _n_suggestions_before = len(self._job_title_suggestions)
                self.create_new_job_title_and_location_suggestions()
                _n_new = len(self._job_title_suggestions) - _n_suggestions_before
                print(f"{Colors.GREEN}Added {_n_new} new suggestions.{Colors.RESET}")
            elif action == "remove":
                to_remove = inquirer.select(
                    message="Select title to remove:",
                    choices=[{"name": t, "value": t} for t in titles] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove:
                    self.user.remove_desired_job_title(to_remove)
            elif action == "regenerate_suggestions":
                self._job_title_suggestions = []
                self.create_new_job_title_and_location_suggestions()

    def configure_job_locations(self):
        """Configure desired job locations."""
        while True:
            clear_screen()
            print_header("Desired Job Locations")
            locations = self.user.desired_job_locations
            print_list("Current locations", locations)
            print()

            if self._job_location_suggestions:
                print_inline_list("Suggested Locations", self._job_location_suggestions)
                print()
                
            choices = [
                {"name": "Add a location manually", "value": "add"},
                {"name": "Add a location from AI suggestions", "value": "use_suggestions"},
                {"name": "Generate more suggestions", "value": "generate_suggestions"}
            ]
            if locations:
                choices.append({"name": "Remove a location", "value": "remove"})
            if self._job_location_suggestions:
                choices.append({"name": "Clear AI suggestions and re-generate", "value": "regenerate_suggestions"})
            choices.append({"name": "← Done", "value": "done"})

            action = inquirer.select(message="Action:", choices=choices).execute()

            if action == "done":
                break
            elif action == "add":
                new_loc = inquirer.text(message="Enter job location:").execute()
                if new_loc:
                    self.user.add_desired_job_location(new_loc)
            elif action == "use_suggestions":
                for _ in range(3):
                    if not self._job_location_suggestions:
                        self.create_new_job_title_and_location_suggestions()
                if not self._job_location_suggestions:
                    print(f"{Colors.RED}Could not generate suggestions{Colors.RESET}")
                if self._job_location_suggestions:
                    choices = [
                        {"name": s, "value": s, "enabled": False}
                        for s in self._job_location_suggestions
                    ]
                    selected = inquirer.checkbox(
                        message="Select locations to add:",
                        choices=choices,
                    ).execute()
                    for loc in selected:
                        self.user.add_desired_job_location(loc)
                        self._job_location_suggestions.remove(loc)
            elif action == "generate_suggestions":
                _n_suggestions_before = len(self._job_location_suggestions)
                self.create_new_job_title_and_location_suggestions()
                _n_new = len(self._job_location_suggestions) - _n_suggestions_before
                print(f"{Colors.GREEN}Added {_n_new} new suggestions.{Colors.RESET}")
            elif action == "remove":
                to_remove = inquirer.select(
                    message="Select location to remove:",
                    choices=[{"name": loc, "value": loc} for loc in locations] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove:
                    self.user.remove_desired_job_location(to_remove)
            elif action == "regenerate_suggestions":
                self._job_location_suggestions = []
                self.create_new_job_title_and_location_suggestions()

    def configure_source_documents(self):
        """Configure source document paths."""
        while True:
            clear_screen()
            print_header("Source Documents")
            paths = self.user.source_document_paths
            print_list("Document paths", paths)
            print()

            action = inquirer.select(
                message="Action:",
                choices=[
                    {"name": "Add a file or folder", "value": "add"},
                    {"name": "Remove a path", "value": "remove"},
                    {"name": "Clear all paths", "value": "clear"},
                    {"name": "← Done", "value": "done"},
                ],
            ).execute()

            if action == "done":
                break
            elif action == "clear":
                self.user.clear_source_document_paths()
                print("Cleared all paths.")
            elif action == "remove":
                if not paths:
                    print("No paths to remove.")
                    continue
                to_remove = inquirer.select(
                    message="Select path to remove:",
                    choices=[{"name": p, "value": p} for p in paths] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove:
                    self.user.remove_source_document_path(to_remove)
                    print(f"Removed: {to_remove}")
            elif action == "add":
                add_type = inquirer.select(
                    message="What do you want to add?",
                    choices=[
                        {"name": "A specific file", "value": "file"},
                        {"name": "A folder (all files inside)", "value": "folder"},
                    ],
                ).execute()

                if add_type == "folder":
                    selected_path = inquirer.filepath(
                        message="Select folder:",
                        default=str(Path.home()),
                        validate=PathValidator(is_dir=True, message="Must be a directory")
                    ).execute()
                    selected_path = str(Path(selected_path).resolve()) + "/*"
                else:
                    selected_path = inquirer.filepath(
                        message="Select file:",
                        default=str(Path.home()),
                        validate=PathValidator(is_file=True, message="Must be a file")
                    ).execute()
                    selected_path = str(Path(selected_path).resolve())

                self.user.add_source_document_path(selected_path)
                print(f"Added: {selected_path}")

        if self.user.source_document_paths:
            self.user.combined_source_documents = combine_documents(self.user.source_document_paths)
    
        if self.user.combined_source_documents:
            print("Generating summary of source documents...")
            summary = summarize_source_documents(combined_documents_as_string(self.user.combined_source_documents))
            if summary:
                self.user.source_document_summary = summary
                print("Summary generated.")
            else:
                print("Could not generate summary.")

    def configure_cover_letter_output_dir(self):
        """Configure cover letter output directory."""
        clear_screen()
        print_header("Cover Letter Output Directory")
        old_dir = self.user.cover_letter_output_dir
        print(f"  {Colors.DIM}Current: {old_dir}{Colors.RESET}\n")

        action = inquirer.select(
            message="Action:",
            choices=[
                {"name": "Keep current directory", "value": "keep"},
                {"name": "Set custom directory", "value": "custom"},
                {"name": "Reset to default", "value": "reset"},
            ],
        ).execute()

        new_dir = None
        if action == "custom":
            new_path = inquirer.filepath(
                message="Select output directory:",
                default=str(Path.home()),
                validate=PathValidator(is_dir=True, message="Must be a directory")
            ).execute()
            self.user.cover_letter_output_dir = str(Path(new_path).resolve())
            new_dir = self.user.cover_letter_output_dir
            print(f"\n{Colors.GREEN}Set output directory to: {new_dir}{Colors.RESET}")
        elif action == "reset":
            self.user.cover_letter_output_dir = ""
            new_dir = self.user.cover_letter_output_dir
            print(f"\n{Colors.GREEN}Reset to default: {new_dir}{Colors.RESET}")

        # Move existing PDFs from old to new directory
        if new_dir and old_dir != new_dir:
            self._move_cover_letter_pdfs(old_dir, new_dir)

    def configure_writing_instructions(self):
        """Configure cover letter writing style instructions."""
        while True:
            clear_screen()
            print_header("Cover Letter Writing Style")

            instructions = self.user.cover_letter_writing_instructions
            print_numbered_list("Instructions", instructions)
            print()

            choices = [
                {"name": "Add instruction", "value": "add"}, 
                {"name": "Remove instruction", "value": "remove"},
                {"name": "Reset (use defaults)", "value": "reset"},
                {"name": "Done", "value": "done"}
            ]

            action = inquirer.select(message="Action:", choices=choices).execute()

            if action == "done":
                break
            elif action == "add":
                instruction = inquirer.text(
                    message="Enter instruction:",
                    validate=lambda x: len(x.strip()) > 0
                ).execute()
                if instruction:
                    instructions.append(instruction.strip())
                    self.user.cover_letter_writing_instructions = instructions
            elif action == "remove":
                to_remove = inquirer.select(
                    message="Select instruction to remove:",
                    choices=[
                        {"name": f"{i}. {inst[:60]}{'...' if len(inst) > 60 else ''}", "value": i-1}
                        for i, inst in enumerate(instructions, 1)
                    ] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove is not None:
                    instructions.pop(to_remove)
                    self.user.cover_letter_writing_instructions = instructions
            elif action == "reset":
                self.user.reset_cover_letter_writing_instructions()
                print(f"\n{Colors.GREEN}Reset writing instructions: using defaults.{Colors.RESET}")
                time.sleep(1)

    def configure_search_instructions(self):
        """Configure search instructions for job search prompts."""
        while True:
            clear_screen()
            print_header("Search Instructions")
            print(f"  {Colors.DIM}These instructions guide AI when generating search queries{Colors.RESET}")
            print(f"  {Colors.DIM}and filtering job results.{Colors.RESET}\n")

            instructions = self.user.search_instructions
            if instructions:
                print_numbered_list("Current instructions", instructions)
            else:
                print(f"  {Colors.DIM}No search instructions set.{Colors.RESET}")
            print()

            choices = [
                {"name": "Add instruction", "value": "add"},
            ]
            if instructions:
                choices.append({"name": "Remove instruction", "value": "remove"})
                choices.append({"name": "Clear all", "value": "clear"})
            choices.append({"name": "Done", "value": "done"})

            action = inquirer.select(message="Action:", choices=choices).execute()

            if action == "done":
                break
            elif action == "add":
                print(f"\n  {Colors.DIM}Examples:{Colors.RESET}")
                print(f"  {Colors.DIM}- Consider fully remote jobs only{Colors.RESET}")
                print(f"  {Colors.DIM}- Exclude contract or temporary positions{Colors.RESET}")
                print(f"  {Colors.DIM}- Focus on companies with 50+ employees{Colors.RESET}\n")
                instruction = inquirer.text(
                    message="Enter instruction:",
                    validate=lambda x: len(x.strip()) > 0
                ).execute()
                if instruction:
                    instructions.append(instruction.strip())
                    self.user.search_instructions = instructions
            elif action == "remove":
                to_remove = inquirer.select(
                    message="Select instruction to remove:",
                    choices=[
                        {"name": f"{i}. {inst[:60]}{'...' if len(inst) > 60 else ''}", "value": i-1}
                        for i, inst in enumerate(instructions, 1)
                    ] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove is not None:
                    instructions.pop(to_remove)
                    self.user.search_instructions = instructions
            elif action == "clear":
                confirm = inquirer.confirm(
                    message="Clear all search instructions?",
                    default=False
                ).execute()
                if confirm:
                    self.user.search_instructions = []
                    print(f"\n{Colors.GREEN}Cleared all search instructions.{Colors.RESET}")
                    time.sleep(1)

    def _move_cover_letter_pdfs(self, old_dir: Path, new_dir: Path):
        """Move cover letter PDFs from old directory to new directory."""
        #TODO: This is business logic that should be in a separate module
        old_dir = Path(old_dir)
        new_dir = Path(new_dir)

        if not old_dir.exists():
            return

        # Find all jobs with cover letter PDFs in the old directory
        moved_count = 0
        for job in self.user.job_handler:
            if job.cover_letter_pdf_path is None:
                continue

            pdf_path = job.cover_letter_pdf_path
            # Check if this PDF is in the old directory
            if pdf_path.parent == old_dir and pdf_path.exists():
                new_pdf_path = new_dir / pdf_path.name
                try:
                    shutil.move(str(pdf_path), str(new_pdf_path))
                    job.set_cover_letter_pdf_path(new_pdf_path)
                    moved_count += 1
                except (OSError, shutil.Error) as e:
                    print(f"{Colors.RED}Failed to move {pdf_path.name}: {e}{Colors.RESET}")

        if moved_count > 0:
                print(f"{Colors.GREEN}✓ Moved {moved_count} cover letter PDF(s) to new directory{Colors.RESET}")

    def configure_ai_credentials(self):
        """Configure AI backend credentials."""
        clear_screen()
        print_header("AI Credentials")

        current = self.user.ai_credentials
        method = current.get("method", "claude_local")
        if method == "claude_local":
            print(f"  {Colors.DIM}Current: Claude CLI (local){Colors.RESET}\n")
        else:
            api_key = current.get("api_key", "")
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            print(f"  {Colors.DIM}Current: OpenAI API ({masked_key}){Colors.RESET}\n")

        choices = [
            {"name": "Claude CLI (local)", "value": "claude_local"},
            {"name": "OpenAI API", "value": "open_ai"},
        ]

        selected = inquirer.select(
            message="Select AI backend:",
            choices=choices,
            default=method,
        ).execute()

        if selected == "claude_local":
            self.user.ai_credentials = {"method": "claude_local"}
        else:
            current_key = current.get("api_key", "") if method == "open_ai" else ""
            api_key = inquirer.secret(
                message="Enter OpenAI API key:",
                default=current_key,
            ).execute()
            if api_key:
                self.user.ai_credentials = {"method": "open_ai", "api_key": api_key}
            else:
                print(f"{Colors.YELLOW}No API key provided, keeping previous setting.{Colors.RESET}")
                return

        print(f"AI credentials updated.")

    def refresh_source_documents(self):
        """Re-read source documents and regenerate summary."""
        service = UserProfileService(on_progress=lambda msg, level: print(msg))
        result = service.refresh_source_documents(self.user)

        if result.success:
            print(f"{Colors.GREEN}✓ {result.message}{Colors.RESET}")
        else:
            print(f"{Colors.RED}{result.message}{Colors.RESET}")

    def refresh_online_presence(self):
        """Fetch online presence and regenerate summary."""
        service = UserProfileService(on_progress=lambda msg, _: print(msg))
        result = service.refresh_online_presence(self.user)

        if result.success:
            print(f"{Colors.GREEN}✓ {result.message}{Colors.RESET}")
        else:
            print(f"{Colors.RED}{result.message}{Colors.RESET}")

    def generate_job_title_and_location_suggestions(self):
        """Use Claude to suggest job titles and locations from source documents."""
        service = UserProfileService(on_progress=lambda msg, _: print(msg))

        existing_titles = list(set(self.user.desired_job_titles) | set(self._job_title_suggestions))
        existing_locations = list(set(self.user.desired_job_locations) | set(self._job_location_suggestions))

        result = service.suggest_job_titles_and_locations(
            self.user,
            existing_titles=existing_titles,
            existing_locations=existing_locations
        )

        if not result.success:
            print(f"{Colors.RED}{result.message}{Colors.RESET}")

        return {"titles": result.data.get("titles", []), "locations": result.data.get("locations", [])}

    def create_new_job_title_and_location_suggestions(self):
        results = self.generate_job_title_and_location_suggestions()
        
        new_titles = [t for t in results.get("titles", []) if t not in self.user.desired_job_titles]
        self._job_title_suggestions = sorted(set(new_titles + self._job_title_suggestions))
        
        new_locations = [t for t in results.get("locations", []) if t not in self.user.desired_job_locations]
        self._job_location_suggestions = sorted(set(new_locations + self._job_location_suggestions))
    
    def generate_comprehensive_summary(self):
        """Generate a comprehensive summary combining all user information."""
        service = UserProfileService(on_progress=lambda msg, _: print(msg))
        result = service.generate_comprehensive_summary(self.user)

        if result.success:
            print(f"{Colors.GREEN}✓ {result.message}{Colors.RESET}")
            if result.data and result.data.get("preview"):
                preview = result.data["preview"]
                if len(self.user.comprehensive_summary) > 500:
                    preview += "..."
                print(f"\nPreview:\n{preview}")
        else:
            print(f"{Colors.RED}{result.message}{Colors.RESET}")

    def view_comprehensive_summary(self):
        """View the full comprehensive summary."""
        clear_screen()
        if not self.user.comprehensive_summary:
            print(f"{Colors.YELLOW}No comprehensive summary generated yet.{Colors.RESET}")
            print("Use 'Generate comprehensive summary' to create one.")
            input("\nPress Enter to continue...")
            return

        print_header("Comprehensive Summary")
        print(self.user.comprehensive_summary)
        print()
        print_thick_line()
        input("\nPress Enter to continue...")

    def review_queries(self):
        """Review and remove search queries with checkbox selection."""
        clear_screen()
        print_header("Review Search Queries")

        queries = list(self.user.query_handler)
        if not queries:
            print(f"  {Colors.DIM}No search queries to review.{Colors.RESET}\n")
            input("Press Enter to continue...")
            return

        # Build checkbox choices with query string and job count
        choices = []
        for q in queries:
            job_count = self.user.query_handler.get_results_count(q.id)
            # Truncate long queries for display
            display_query = q.query[:70] + "..." if len(q.query) > 70 else q.query
            label = f"{display_query} ({job_count} jobs found)"
            choices.append({"name": label, "value": q.id, "enabled": True})

        print(f"  {Colors.DIM}Uncheck queries to remove them.{Colors.RESET}\n")

        selected_ids = inquirer.checkbox(
            message="Keep these queries:",
            choices=choices,
        ).execute()

        # Find which queries were unchecked (to be removed)
        all_ids = {q.id for q in queries}
        selected_set = set(selected_ids)
        to_remove = list(all_ids - selected_set)

        if to_remove:
            self.user.query_handler.remove(to_remove)
            print(f"\n{Colors.GREEN}✓ Removed {len(to_remove)} queries.{Colors.RESET}")
            print(f"  {Colors.DIM}{len(self.user.query_handler)} queries remaining.{Colors.RESET}\n")
        else:
            print(f"\n{Colors.DIM}No queries removed.{Colors.RESET}\n")

        input("Press Enter to continue...")

    def create_search_queries(self):
        """Create search queries from the user's information."""
        service = UserProfileService(on_progress=lambda msg, _: print(msg))
        result = service.create_search_queries(self.user)

        if result.success:
            print(f"{Colors.GREEN}✓ {result.message}{Colors.RESET}")
        else:
            print(f"{Colors.RED}{result.message}{Colors.RESET}")

    def user_info_menu(self):
        """Show user info and provide edit options."""
        while True:
            clear_screen()
            self.display_user_info()
            print()
            print_thick_line()
            print()

            action = inquirer.select(
                message="What would you like to do?",
                choices=[
                    {"name": "Edit name", "value": self.configure_name},
                    {"name": "Edit email", "value": self.configure_email},
                    {"name": "Edit credentials", "value": self.configure_credentials},
                    {"name": "Edit websites", "value": self.configure_websites},
                    {"name": "Edit source documents (CV etc.)", "value": self.configure_source_documents},
                    {"name": "Edit job titles", "value": self.configure_job_titles},
                    {"name": "Edit job locations", "value": self.configure_job_locations},
                    {"name": "Edit cover letter output directory", "value": self.configure_cover_letter_output_dir},
                    {"name": "Edit cover letter writing style", "value": self.configure_writing_instructions},
                    {"name": "Edit search instructions", "value": self.configure_search_instructions},
                    {"name": "Edit AI credentials", "value": self.configure_ai_credentials},
                    {"name": "─" * 30, "value": None, "disabled": ""},
                    {"name": "Refresh source documents", "value": self.refresh_source_documents},
                    {"name": "Refresh online presence", "value": self.refresh_online_presence},
                    {"name": "✨ Generate comprehensive summary", "value": self.generate_comprehensive_summary},
                    {"name": "📄 View comprehensive summary", "value": self.view_comprehensive_summary},
                    {"name": "─" * 30, "value": None, "disabled": ""},
                    {"name": "← Back to main menu", "value": "back"},
                ],
            ).execute()

            if action == "back":
                break
            elif action:
                action()

    def search_menu(self):
        """Search for jobs menu."""
        while True:
            clear_screen()
            print_header("Search for Jobs")

            num_queries = len(self.user.query_handler)
            num_jobs = len(self.user.job_handler)

            print(f"  {Colors.DIM}Search queries: {num_queries}{Colors.RESET}")
            print(f"  {Colors.DIM}Jobs found: {num_jobs}{Colors.RESET}\n")

            if num_queries == 0:
                print(f"{Colors.YELLOW}No search queries configured.{Colors.RESET}")
                generate = inquirer.confirm(
                    message="Would you like to generate search queries now?",
                    default=True
                ).execute()
                if generate:
                    self.create_search_queries()
                    num_queries = len(self.user.query_handler)
                    if num_queries == 0:
                        print(f"\n{Colors.DIM}No queries generated. Configure job titles and locations first.{Colors.RESET}\n")
                        return
                    continue
                else:
                    return

            print()
            print_thick_line()
            print()

            num_pending = self.user.job_handler.number_pending
            choices=[
                    {"name": f"Search using all queries ({num_queries})", "value": "search_all"},
                    {"name": "Search using selected queries", "value": "search_selected"},
                    {"name": "Review queries", "value": "review"},
                    {"name": "Generate new queries", "value": "generate"}
                ]

            if num_pending:
                choices.append({"name": f"○ View pending jobs ({num_pending})", "value": "jobs_pending"})

            choices.append({"name": "← Back to main menu", "value": "back"})

            action = inquirer.select(
                message="What would you like to do?",
                choices=choices
            ).execute()

            if action == "back":
                return
            elif action == "review":
                self.review_queries()
            elif action == "generate":
                self.create_search_queries()
            elif action == "jobs_pending":
                self.jobs_menu(job_type="pending")
            elif action == "search_all":
                fetch_desc = inquirer.confirm(
                    message="Fetch full job descriptions? (slower but more complete)",
                    default=True
                ).execute()
                self.job_searcher.search(fetch_descriptions=fetch_desc)
                print()
            elif action == "search_selected":
                # Show checkbox to select specific queries
                queries = list(self.user.query_handler)
                query_choices = []
                for q in queries:
                    display_query = q.query[:70] + "..." if len(q.query) > 70 else q.query
                    query_choices.append({"name": display_query, "value": q.id, "enabled": False})

                selected_ids = inquirer.checkbox(
                    message="Select queries to search with:",
                    choices=query_choices,
                ).execute()

                if not selected_ids:
                    print(f"\n{Colors.DIM}No queries selected.{Colors.RESET}\n")
                    input("Press Enter to continue...")
                    continue

                fetch_desc = inquirer.confirm(
                    message="Fetch full job descriptions? (slower but more complete)",
                    default=True
                ).execute()
                self.job_searcher.search(query_ids=selected_ids, fetch_descriptions=fetch_desc)
                print()
  
    def jobs_menu(self, job_type: str = "all"):
        """View and manage found jobs.

        Args:
            job_type: Filter jobs by type - "pending", "in_progress", "applied", "discarded", or "all"
        """
        while True:
            # Filter jobs based on type (refresh each iteration in case status changed)
            if job_type == "pending":
                jobs = [j for j in self.user.job_handler if j.status == JobStatus.PENDING]
                header_title = "Pending Jobs"
                empty_msg = "No pending jobs."
            elif job_type == "in_progress":
                jobs = [j for j in self.user.job_handler if j.status == JobStatus.IN_PROGRESS]
                header_title = "In Progress Jobs"
                empty_msg = "No jobs in progress."
            elif job_type == "applied":
                jobs = [j for j in self.user.job_handler if j.status == JobStatus.APPLIED]
                header_title = "Applied Jobs"
                empty_msg = "No applied jobs yet."
            elif job_type == "discarded":
                jobs = [j for j in self.user.job_handler if j.status == JobStatus.DISCARDED]
                header_title = "Discarded Jobs"
                empty_msg = "No discarded jobs."
            else:
                jobs = list(self.user.job_handler)
                header_title = "All Jobs"
                empty_msg = "No jobs found yet."

            clear_screen()
            print_header(header_title)

            if not jobs:
                print(f"  {Colors.DIM}{empty_msg}{Colors.RESET}\n")
                input("Press Enter to continue...")
                return

            print_status_summary(
                applied=self.user.job_handler.number_applied,
                in_progress=self.user.job_handler.number_in_progress,
                pending=self.user.job_handler.number_pending,
                discarded=self.user.job_handler.number_discarded
            )
            print()

            # Display jobs as cards
            for i, job in enumerate(jobs, 1):
                display_job_card(job, i)

            print()
            print_thick_line()
            print()

            user_input = inquirer.text(
                message=f"Enter job number (1-{len(jobs)}) or 'b' to go back:",
            ).execute()

            if user_input.lower() in ("b", "back", ""):
                break
            
            if user_input == "DELETE":
                for job in jobs:
                    self.user.job_handler.delete_job(job_id=job.id)

            try:
                index = int(user_input) - 1
                if 0 <= index < len(jobs):
                    JobOptions(user=self.user, job_id=jobs[index].id).menu()
                else:
                    print(f"\n{Colors.RED}Invalid number. Please enter 1-{len(jobs)}.{Colors.RESET}\n")
                    input("Press Enter to continue...")
            except ValueError:
                print(f"\n{Colors.RED}Invalid input. Enter a number or 'b' to go back.{Colors.RESET}\n")
                input("Press Enter to continue...")

    def add_job_menu(self):
        """Add a job manually or from a URL."""
        from search_jobs import fetch_full_description

        clear_screen()
        print_header("Add a Job")

        action = inquirer.select(
            message="How would you like to add the job?",
            choices=[
                {"name": "Paste a job posting URL (auto-scrape)", "value": "url"},
                {"name": "Enter details manually", "value": "manual"},
                {"name": "← Cancel", "value": "cancel"},
            ],
        ).execute()

        if action == "cancel":
            return

        if action == "url":
            url = inquirer.text(
                message="Job posting URL:",
            ).execute()

            if not url:
                print(f"\n{Colors.YELLOW}No URL entered.{Colors.RESET}\n")
                input("Press Enter to continue...")
                return

            print(f"\n{Colors.CYAN}Fetching job description...{Colors.RESET}")
            full_description = fetch_full_description(url)

            if full_description:
                print(f"{Colors.GREEN}✓ Got {len(full_description)} characters{Colors.RESET}\n")
            else:
                print(f"{Colors.YELLOW}Could not extract description. You can add it manually later.{Colors.RESET}\n")

            # Prompt for required fields
            company = inquirer.text(
                message="Company name:",
            ).execute()

            if not company:
                print(f"\n{Colors.RED}Company name is required.{Colors.RESET}\n")
                input("Press Enter to continue...")
                return

            title = inquirer.text(
                message="Job title:",
            ).execute()

            if not title:
                print(f"\n{Colors.RED}Job title is required.{Colors.RESET}\n")
                input("Press Enter to continue...")
                return

            location = inquirer.text(
                message="Location (optional):",
            ).execute()

            # Create the job
            job = self.user.job_handler.add(
                company=company,
                title=title,
                link=url,
                location=location or "",
                full_description=full_description or "",
            )
            print(f"\n{Colors.GREEN}✓ Added: {job.title} at {job.company}{Colors.RESET}\n")

            # Open the job details menu
            edit_now = inquirer.confirm(
                message="Edit job details now?",
                default=True
            ).execute()

            if edit_now:
                JobOptions(user=self.user, job_id=job.id).menu()

        elif action == "manual":
            # Prompt for required fields
            company = inquirer.text(
                message="Company name:",
            ).execute()

            if not company:
                print(f"\n{Colors.RED}Company name is required.{Colors.RESET}\n")
                input("Press Enter to continue...")
                return

            title = inquirer.text(
                message="Job title:",
            ).execute()

            if not title:
                print(f"\n{Colors.RED}Job title is required.{Colors.RESET}\n")
                input("Press Enter to continue...")
                return

            link = inquirer.text(
                message="Job posting URL (optional):",
            ).execute()

            location = inquirer.text(
                message="Location (optional):",
            ).execute()

            # Create the job
            job = self.user.job_handler.add(
                company=company,
                title=title,
                link=link or "",
                location=location or "",
            )
            print(f"\n{Colors.GREEN}✓ Added: {job.title} at {job.company}{Colors.RESET}\n")

            # Open the job details menu to add more info
            edit_now = inquirer.confirm(
                message="Add more details now?",
                default=True
            ).execute()

            if edit_now:
                JobOptions(user=self.user, job_id=job.id).menu()

    def main_menu(self):
        """Main application menu."""
        
                
        if self.user.is_new_user():
            self.first_time_setup()
            
        while True:
            clear_screen()
            print(ASCII_ART_JOBSEARCH)
            
            print_header(f"Welcome {self.user.name}")

            num_pending = self.user.job_handler.number_pending
            num_in_progress = self.user.job_handler.number_in_progress
            num_applied = self.user.job_handler.number_applied
            num_discarded = self.user.job_handler.number_discarded
            num_total = len(self.user.job_handler)

            if num_total:
                print_status_summary(
                    applied=num_applied,
                    in_progress=num_in_progress,
                    pending=num_pending,
                    discarded=num_discarded
                )
                print()

            choices=[
                {"name": "View/Edit User Info", "value": "user"},
                {"name": "Search for Jobs", "value": "search"}
            ]
            if num_pending:
                choices.append({"name": f"○ View pending jobs ({num_pending})", "value": "jobs_pending"})
            if num_in_progress:
                choices.append({"name": f"▶ View in progress jobs ({num_in_progress})", "value": "jobs_in_progress"})
            if num_applied:
                choices.append({"name": f"✓ View applied jobs ({num_applied})", "value": "jobs_applied"})
            if num_discarded:
                choices.append({"name": f"✗ View discarded jobs ({num_discarded})", "value": "jobs_discarded"})
            choices.extend([
                {"name": "Add a job manually", "value": "add_job"},
                {"name": "Settings", "value": "settings"},
                {"name": "Exit", "value": "exit"}
                ])
            action = inquirer.select(
                message="Select an option:",
                choices=choices
            ).execute()

            if action == "exit":
                print(f"\n{Colors.DIM}Goodbye!{Colors.RESET}\n")
                break
            elif action == "user":
                self.user_info_menu()
            elif action == "search":
                self.search_menu()
            elif action == "jobs_pending":
                self.jobs_menu(job_type="pending")
            elif action == "jobs_in_progress":
                self.jobs_menu(job_type="in_progress")
            elif action == "jobs_applied":
                self.jobs_menu(job_type="applied")
            elif action == "jobs_discarded":
                self.jobs_menu(job_type="discarded")
            elif action == "add_job":
                self.add_job_menu()
            elif action == "settings":
                print(f"\n{Colors.DIM}Settings coming soon...{Colors.RESET}\n")
