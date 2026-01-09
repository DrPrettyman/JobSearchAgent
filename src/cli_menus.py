"""CLI menu functions for JobSearch application."""

import json
import re
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.validator import PathValidator

from data_handlers import User, Job, Jobs
from cli_utils import (
    Colors,
    ASCII_ART_JOBSEARCH,
    clear_screen,
    print_header,
    print_section,
    print_field,
    print_list,
    hyperlink,
    display_job_card,
    display_job_detail
)
from utils import (
    combined_documents_as_string,
    run_claude,
    extract_url_slug,
    summarize_source_documents,
    summarize_online_presence,
    combine_documents,
    extract_json_from_response,
)
from online_presence import fetch_online_presence
from search_jobs import search
from cover_letter_writer import LetterWriter, generate_cover_letter_topics, generate_cover_letter_body

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
        writer = LetterWriter(
            company=self.job.company,
            title=self.job.title,
            cover_letter_body=self.job.cover_letter_body,
            user_name=self.user.name,
            user_email=self.user.email,
            user_linkedin_ext=self.user.linkedin_extension,
            user_credentials=self.user.credentials,
            user_website=self.user.websites[0] if self.user.websites else None,
            addressee=self.job.addressee
        )
               
        pdf_path = writer.save_pdf(output_dir=self.user.cover_letter_output_dir)
        if pdf_path is None:
            print(f"{Colors.RED}Failed to compile cover letter as PDF file.{Colors.RESET}\n")
            return

        self.job.set_cover_letter_pdf_path(pdf_path.resolve())
        self.user.job_handler.save()
        
    def generate_cover_letter_for_job(self):
        """Generate cover letter content for a job."""
        # Use full description if available, otherwise use summary
        job_description = self.job.full_description or self.job.description

        if not job_description:
            print(f"\n{Colors.RED}Cannot generate: no job description available.{Colors.RESET}\n")
            return

        # Prefer comprehensive summary, fall back to combined docs
        user_background = self.user.comprehensive_summary or combined_documents_as_string(self.user.combined_source_documents)

        if not user_background:
            print(f"\n{Colors.RED}Cannot generate: no source documents configured.{Colors.RESET}")
            print(f"{Colors.DIM}Add your resume/CV in User Info first.{Colors.RESET}\n")
            return

        if not self.user.comprehensive_summary:
            print(f"{Colors.YELLOW}Tip: Generate a comprehensive summary for better cover letters.{Colors.RESET}")

        # Step 1: Generate cover letter topics (if not already present)
        if not self.job.cover_letter_topics:
            print(f"\n{Colors.CYAN}Analyzing job description...{Colors.RESET}")
            topics = generate_cover_letter_topics(
                job_description=job_description,
                user_background=user_background
            )
            if not topics:
                print(f"{Colors.RED}Failed to analyze job description.{Colors.RESET}\n")
                return
            self.job.cover_letter_topics = topics
            self.user.job_handler.save()
            print(f"{Colors.GREEN}✓ Identified {len(topics)} key topics{Colors.RESET}")

        # Step 2: Generate cover letter body from topics
        print(f"{Colors.CYAN}Generating cover letter...{Colors.RESET}")

        body = generate_cover_letter_body(
            job_title=self.job.title,
            company=self.job.company,
            job_description=job_description,
            user_background=user_background,
            cover_letter_topics=self.job.cover_letter_topics
        )

        if body:
            self.job.cover_letter_body = body
            self.user.job_handler.save()
            print(f"{Colors.GREEN}✓ Cover letter generated!{Colors.RESET}\n")
            self.export_pdf_cover_letter()
        else:
            print(f"{Colors.RED}Failed to generate cover letter.{Colors.RESET}\n")
            
    def menu(self):
        """View and manage a single job."""
        while True:
            clear_screen()
            display_job_detail(self.job)

            choices = []
            if not self.job.applied:
                choices.append({"name": "✓ Mark as applied", "value": "apply"})
            else:
                choices.append({"name": "○ Mark as not applied", "value": "unapply"})

            if self.job.link:
                choices.append({"name": "🔗 Open job link", "value": "open_link"})
                
            if self.job.cover_letter_body:
                choices.append({"name": "🔄 Regenerate cover letter", "value": "cover_letter_generate"})
                choices.append({"name": "📄 Copy plain text cover letter to clipboard", "value": "cover_letter_text_clipboard"})
            else:
                choices.append({"name": "📄 Generate cover letter", "value": "cover_letter_generate"})
            
            if self.job.cover_letter_pdf_path is not None:
                choices.append({"name": "📄 Open PDF cover letter", "value": "cover_letter_open"})
                choices.append({"name": "📄 Copy PDF cover letter to clipboard", "value": "cover_letter_pdf_clipboard"})
            else:
                if self.job.cover_letter_body:
                    choices.append({"name": "📄 Retry PDF cover letter export", "value": "cover_letter_pdf_export"})
            
            choices.append({"name": "← Back to jobs list", "value": "back"})

            action = inquirer.select(
                message="What would you like to do?",
                choices=choices,
            ).execute()

            if action == "back":
                break
            elif action == "mark as applied":
                self.job.applied = True
                print(f"\n{Colors.GREEN}✓ Marked as applied!{Colors.RESET}\n")
            elif action == "unmark as applied":
                self.job.applied = False
                print(f"\n{Colors.YELLOW}○ Marked as not applied.{Colors.RESET}\n")
            elif action == "open_link":
                import webbrowser
                webbrowser.open(self.job.link)
                print(f"\n{Colors.DIM}Opening in browser...{Colors.RESET}\n")
            elif action == "cover_letter_generate":
                self.generate_cover_letter_for_job()
            elif action == "cover_letter_open":
                import subprocess
                subprocess.run(['open', str(self.job.cover_letter_pdf_path)])
                print(f"\n{Colors.DIM}Opening PDF...{Colors.RESET}\n")
            elif action == "cover_letter_text_clipboard":
                import subprocess
                letter_text = self.job.cover_letter_full_text(name_for_letter=self.user.name_with_credentials)
                subprocess.run(['pbcopy'], input=letter_text.encode(), check=True)
                print(f"\n{Colors.GREEN}✓ Cover letter copied to clipboard{Colors.RESET}\n")
            elif action == "cover_letter_pdf_clipboard":
                import subprocess
                # Use osascript to copy file to clipboard on macOS
                path = str(self.job.cover_letter_pdf_path)
                script = f'set the clipboard to (read (POSIX file "{path}") as «class PDF »)'
                subprocess.run(['osascript', '-e', script], check=True)
                print(f"\n{Colors.GREEN}✓ PDF copied to clipboard{Colors.RESET}\n")
            elif action == "cover_letter_pdf_export":
                self.export_pdf_cover_letter()
       

class UserOptions:
    """Menu for viewing and editing user information."""

    def __init__(self, user: User):
        self.user = user
        self._job_title_suggestions = []
        self._job_location_suggestions = []
        
    def first_time_setup(self):
        """Guided setup flow for first-time users."""
        clear_screen()
        print(f"{Colors.CYAN}{ASCII_ART_JOBSEARCH}{Colors.RESET}")
        print(ASCII_ART_JOBSEARCH)
        print(f"  {Colors.DIM}Let's set up your profile to find the perfect job.{Colors.RESET}\n")

        # Step 1: Basic info
        print_section("Step 1: Basic Information")
        self.configure_name()
        self.configure_email()
        self.configure_credentials()

        # Step 2: Online presence
        print_section("Step 2: Online Presence")
        self.configure_linkedin()
        self.configure_websites()

        # Fetch online presence if URLs configured
        has_online_urls = self.user.linkedin_extension or self.user.websites
        if has_online_urls:
            fetch = inquirer.confirm(
                message="Fetch content from your online profiles?",
                default=True
            ).execute()
            if fetch:
                self.refresh_online_presence()

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
                self.suggest_from_documents()

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
        print_section("Basic Information")
        print_field("Name", self.user.name_with_credentials if self.user.name else "")
        print_field("Email", self.user.email)
        print_field("LinkedIn", self.user.linkedin_url if self.user.linkedin_extension else "")
        print()

        # Websites
        if self.user.websites:
            print_section("Websites")
            for site in self.user.websites:
                print(f"  {Colors.GREEN}•{Colors.RESET} {site}")
            print()

        # Information sources
        print_section("Information Sources")
        for path in self.user.source_document_paths:
            print(f"  {Colors.GREEN}•{Colors.RESET} {path}")
        for entry in self.user.online_presence:
            site = entry.get("site", "Unknown")
            time_fetched = entry.get("time_fetched", "")
            if entry.get("success"):
                _content_len = len(entry.get("content", ""))
                fetched_summary = f"Fetched: {time_fetched[:10]} ({_content_len} chars)"
            else:
                fetched_summary = f"Unable to fetch (attempted: {time_fetched})"
            print(f"  {Colors.GREEN}•{Colors.RESET} {site} {Colors.DIM}{fetched_summary}{Colors.RESET}")
            
        
        if self.user.source_document_summary:
            print(f"\n  {Colors.DIM}Document Summary:{Colors.RESET} {self.user.source_document_summary}")
        if self.user.online_presence_summary:
            print(f"\n  {Colors.DIM}Online Summary:  {Colors.RESET} {self.user.online_presence_summary}")
        print()

        # Comprehensive Summary
        print_section("Comprehensive Summary")
        if self.user.comprehensive_summary:
            preview = self.user.comprehensive_summary[:300]
            if len(self.user.comprehensive_summary) > 300:
                preview += "..."
            print(f"  {Colors.GREEN}✓ Generated{Colors.RESET} ({len(self.user.comprehensive_summary)} chars)")
            print(f"  {Colors.DIM}{preview}{Colors.RESET}")
        else:
            print(f"  {Colors.YELLOW}○ Not generated{Colors.RESET}")
            print(f"  {Colors.DIM}Generate to improve cover letter quality{Colors.RESET}")
        print()
        
        # Job Preferences
        print_section("Job Preferences")
        print_list("Desired Titles", self.user.desired_job_titles)
        print()
        print_list("Desired Locations", self.user.desired_job_locations)
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
        self.user.save()

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
        self.user.save()

    def configure_credentials(self):
        """Configure user's credentials/titles."""
        clear_screen()
        print_header("Credentials")
        current = self.user.credentials
        if current:
            print(f"  {Colors.DIM}Current: {', '.join(current)}{Colors.RESET}\n")
        else:
            print(f"  {Colors.DIM}No credentials set{Colors.RESET}\n")

        choices = [
            {"name": cred, "value": cred, "enabled": cred in current}
            for cred in CREDENTIAL_OPTIONS
        ]
        selected = inquirer.checkbox(
            message="Select your credentials (in order of precedence):",
            choices=choices,
        ).execute()
        self.user.credentials = selected
        self.user.save()

    def configure_linkedin(self):
        """Configure LinkedIn profile."""
        clear_screen()
        print_header("LinkedIn")
        current = self.user.linkedin_extension
        if current:
            print(f"  {Colors.DIM}Current: {self.user.linkedin_url}{Colors.RESET}\n")
        else:
            print(f"  {Colors.DIM}Not configured{Colors.RESET}\n")

        value = inquirer.text(
            message="LinkedIn URL or username:",
            default=current,
        ).execute()
        if value:
            self.user.linkedin_extension = extract_url_slug(value)
        else:
            self.user.linkedin_extension = ""
        self.user.save()

    def configure_websites(self):
        """Configure personal websites/portfolios."""
        websites_before = set(self.user.all_websites)
        while True:
            clear_screen()
            print_header("Websites")
            sites = self.user.websites
            if sites:
                for s in sites:
                    print(f"  {Colors.GREEN}•{Colors.RESET} {s}")
                print()
            else:
                print(f"  {Colors.DIM}No websites configured{Colors.RESET}\n")

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

        # Check for LinkedIn URLs in websites
        linkedin_urls = [s for s in self.user.websites if "linkedin.com" in s.lower()]
        for url in linkedin_urls:
            parsed = extract_url_slug(url)
            if self.user.linkedin_extension:
                self.user.remove_website(url)
                print("Removed LinkedIn URL from websites (already configured)")
            else:
                self.user.linkedin_extension = parsed
                self.user.remove_website(url)
                print(f"Moved LinkedIn URL to dedicated field: {parsed}")
        self.user.save()
        
        websites_after = set(self.user.all_websites)
        
        if websites_before != websites_after:
            self.refresh_online_presence

    def configure_job_titles(self):
        """Configure desired job titles."""
        while True:
            clear_screen()
            print_header("Job Titles")
            titles = self.user.desired_job_titles
            if titles:
                for t in titles:
                    print(f"  {Colors.GREEN}•{Colors.RESET} {t}")
                print()
            else:
                print(f"  {Colors.DIM}No job titles configured{Colors.RESET}\n")

            choices = [
                {"name": "Add a title manually", "value": "add"},
                {"name": "Add a title from AI suggestions", "value": "add"}
            ]
            if titles:
                choices.append({"name": "Remove a title", "value": "remove"})
            choices.append({"name": "← Done", "value": "done"})

            action = inquirer.select(message="Action:", choices=choices).execute()

            if action == "done":
                break
            elif action == "add":
                new_title = inquirer.text(message="Enter job title:").execute()
                if new_title:
                    self.user.add_desired_job_title(new_title)
            elif action == "remove":
                to_remove = inquirer.select(
                    message="Select title to remove:",
                    choices=[{"name": t, "value": t} for t in titles] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove:
                    self.user.remove_desired_job_title(to_remove)
        self.user.save()

    def configure_job_locations(self):
        """Configure desired job locations."""
        while True:
            clear_screen()
            print_header("Job Locations")
            locations = self.user.desired_job_locations
            if locations:
                for loc in locations:
                    print(f"  {Colors.GREEN}•{Colors.RESET} {loc}")
                print()
            else:
                print(f"  {Colors.DIM}No job locations configured{Colors.RESET}\n")

            choices = [{"name": "Add a location", "value": "add"}]
            if locations:
                choices.append({"name": "Remove a location", "value": "remove"})
            choices.append({"name": "← Done", "value": "done"})

            action = inquirer.select(message="Action:", choices=choices).execute()

            if action == "done":
                break
            elif action == "add":
                new_loc = inquirer.text(message="Enter job location:").execute()
                if new_loc:
                    self.user.add_desired_job_location(new_loc)
            elif action == "remove":
                to_remove = inquirer.select(
                    message="Select location to remove:",
                    choices=[{"name": loc, "value": loc} for loc in locations] + [{"name": "Cancel", "value": None}],
                ).execute()
                if to_remove:
                    self.user.remove_desired_job_location(to_remove)
        self.user.save()

    def configure_source_documents(self):
        """Configure source document paths."""
        while True:
            clear_screen()
            print_header("Source Documents")
            paths = self.user.source_document_paths
            if paths:
                for p in paths:
                    print(f"  {Colors.GREEN}•{Colors.RESET} {p}")
                print()
            else:
                print(f"  {Colors.DIM}No source documents configured{Colors.RESET}\n")

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
                        validate=PathValidator(is_dir=True, message="Must be a directory")
                    ).execute()
                    selected_path = str(Path(selected_path).resolve()) + "/*"
                else:
                    selected_path = inquirer.filepath(
                        message="Select file:",
                        validate=PathValidator(is_file=True, message="Must be a file")
                    ).execute()
                    selected_path = str(Path(selected_path).resolve())

                self.user.add_source_document_path(selected_path)
                print(f"Added: {selected_path}")

        self.user.save()
        if self.user.source_document_paths:
            self.user.combined_source_documents = combine_documents(self.user.source_document_paths)
            self.user.save()

        if self.user.combined_source_documents:
            print("Generating summary of source documents...")
            summary = summarize_source_documents(combined_documents_as_string(self.user.combined_source_documents))
            if summary:
                self.user.source_document_summary = summary
                self.user.save()
                print("Summary generated.")
            else:
                print("Could not generate summary.")

    def configure_cover_letter_output_dir(self):
        """Configure cover letter output directory."""
        clear_screen()
        print_header("Cover Letter Output Directory")
        current = self.user.cover_letter_output_dir
        print(f"  {Colors.DIM}Current: {current}{Colors.RESET}\n")

        action = inquirer.select(
            message="Action:",
            choices=[
                {"name": "Keep current directory", "value": "keep"},
                {"name": "Set custom directory", "value": "custom"},
                {"name": "Reset to default", "value": "reset"},
            ],
        ).execute()

        if action == "custom":
            new_path = inquirer.filepath(
                message="Select output directory:",
                validate=PathValidator(is_dir=True, message="Must be a directory")
            ).execute()
            self.user.cover_letter_output_dir = str(Path(new_path).resolve())
            self.user.save()
            print(f"Set output directory to: {self.user.cover_letter_output_dir}")
        elif action == "reset":
            self.user.cover_letter_output_dir = ""
            self.user.save()
            print(f"Reset to default: {self.user.cover_letter_output_dir}")

    def refresh_source_documents(self):
        """Re-read source documents and regenerate summary."""
        if not self.user.source_document_paths:
            print("No source documents configured.")
            return

        print("Re-reading source documents...")
        self.user.combined_source_documents = combine_documents(self.user.source_document_paths)
        self.user.save()

        if self.user.combined_source_documents:
            print("Generating summary...")
            summary = summarize_source_documents(combined_documents_as_string(self.user.combined_source_documents))
            if summary:
                self.user.source_document_summary = summary
                self.user.save()
                print("Summary updated.")
            else:
                print("Could not generate summary.")
        else:
            print("No content found in source documents.")

    def refresh_online_presence(self):
        """Fetch online presence and regenerate summary."""
        urls = []
        if self.user.linkedin_url:
            urls.append(self.user.linkedin_url)
        urls.extend(self.user.websites)

        if not urls:
            print("No online presence URLs configured.")
            return

        print("Fetching online presence...")
        results = fetch_online_presence(urls)

        self.user.clear_online_presence()
        for entry in results:
            self.user.add_online_presence(
                site=entry["site"], 
                content=entry["content"], 
                time_fetched=entry["time_fetched"],
                success=entry["success"]
                )

        if self.user.online_presence:
            print("Generating summary...")
            summary = summarize_online_presence(self.user.online_presence)
            if summary:
                self.user.online_presence_summary = summary
            else:
                print("Could not generate summary.")

        self.user.save()
        print(f"Fetched {len(results)} profiles.")

    def suggest_from_documents(self):
        """Use Claude to suggest job titles and locations from source documents."""
        user_background = self.user.comprehensive_summary or combined_documents_as_string(self.user.combined_source_documents)

        if not user_background:
            print("No source documents or comprehensive summary available.")
            return

        print("Analyzing your background to suggest job titles and locations...")

        prompt = f"""Analyze the following CV/resume documents and suggest:
1. A list of 5-10 job titles this person would be suitable for
2. A list of 3-5 preferred job locations based on any hints in the documents. Example locations ["Manchester", "UK, Remote", "Europe, Remote"]

Respond ONLY with valid JSON in this exact format, no other text:
{{"job_titles": ["Title 1", "Title 2"], "job_locations": ["Location 1", "Location 2"]}}

Background:
{user_background}"""

        success, response = run_claude(prompt, timeout=180)

        if not success:
            print(f"Claude analysis failed: {response}")
            return

        try:
            json_str = extract_json_from_response(response)
            suggestions = json.loads(json_str)
            suggested_titles = suggestions.get("job_titles", [])
            suggested_locations = suggestions.get("job_locations", [])

            if suggested_titles:
                selected_titles = inquirer.checkbox(
                    message="Select job titles to add:",
                    choices=[{"name": t, "value": t, "enabled": True} for t in suggested_titles],
                ).execute()
                for title in selected_titles:
                    self.user.add_desired_job_title(title)

            if suggested_locations:
                selected_locations = inquirer.checkbox(
                    message="Select job locations to add:",
                    choices=[{"name": loc, "value": loc, "enabled": True} for loc in suggested_locations],
                ).execute()
                for loc in selected_locations:
                    self.user.add_desired_job_location(loc)

            self.user.save()

        except json.JSONDecodeError:
            print("Could not parse Claude's response.")

    def generate_comprehensive_summary(self):
        """Generate a comprehensive summary combining all user information."""
        source_docs = combined_documents_as_string(self.user.combined_source_documents)

        online_content = ""
        if self.user.online_presence:
            online_parts = []
            for entry in self.user.online_presence:
                site = entry.get("site", "Unknown")
                content = entry.get("content", "")
                if content:
                    online_parts.append(f"[{site}]\n{content}")
            online_content = "\n\n".join(online_parts)

        if not source_docs and not online_content:
            print("No source documents or online presence data available.")
            return

        print("Generating comprehensive summary...")

        prompt = f"""Create a comprehensive professional summary from the following information.

SOURCE DOCUMENTS (CV, resume, etc.):
{source_docs}

ONLINE PRESENCE (LinkedIn, GitHub, portfolio):
{online_content}

Create a COMPREHENSIVE summary that includes:
1. Professional summary/headline
2. COMPLETE work experience with:
   - Company names
   - Job titles
   - Employment dates (month/year to month/year)
   - Key responsibilities and achievements
3. COMPLETE academic background with:
   - Institutions
   - Degrees and fields of study
   - Graduation dates (if available)
   - Notable achievements (publications, awards)
4. Technical skills (categorized)
5. Certifications and credentials
6. Languages (if mentioned)
7. Notable projects or portfolio items

IMPORTANT:
- Include ALL dates mentioned (employment periods, graduation years, etc.)
- Be precise with job titles and company names
- Don't summarize away important details
- Keep all quantified achievements (metrics, percentages, etc.)
- Maintain chronological order for experience and education
- If information is missing or unclear, note it rather than guessing

Return the summary in a clean, structured markdown text format (not JSON). Begin with the heading '# PROFESSIONAL SUMMARY'.
The summary should be thorough enough to write tailored cover letters without needing the original documents."""

        success, response = run_claude(prompt, timeout=300)

        if not success or not isinstance(response, str):
            print(f"Failed to generate summary: {response}")
            return
        response = response.strip()
        if not response:
            print(f"Failed to generate summary")
            return

        # Truncate to start at "# PROFESSIONAL SUMMARY" if present (removes preamble)
        heading = "# PROFESSIONAL SUMMARY"
        if heading in response:
            response = response[response.index(heading):]
            
        response = re.sub(r"(?<=[0-9A-Za-z])([.?!\"\']?)[^0-9A-Za-z]+$", r"\1", response)

        self.user.comprehensive_summary = response
        self.user.save()
        print("Comprehensive summary generated and saved.")

        preview = self.user.comprehensive_summary[:500]
        if len(self.user.comprehensive_summary) > 500:
            preview += "..."
        print(f"\nPreview:\n{preview}")

    def create_search_queries(self):
        """Create search queries from the user's information."""
        if not self.user.desired_job_titles:
            print("No job titles configured. Configure job titles first.")
            return

        if not self.user.desired_job_locations:
            print("No job locations configured. Configure job locations first.")
            return

        print("Generating search queries...")

        user_background = self.user.comprehensive_summary or combined_documents_as_string(self.user.combined_source_documents)

        prompt = f"""Based on this job seeker's profile, create 30 effective job search queries.

Job titles of interest: {self.user.desired_job_titles}
Preferred locations: {self.user.desired_job_locations}

Background summary:
{user_background}

Create varied queries using:
- Different job title variations and related roles
- Different location combinations
- Site-specific searches (site:linkedin.com/jobs, site:lever.co, site:greenhouse.io, site:weworkremotely.com, site:jobs.ashbyhq.com)
- Industry/tech stack keywords relevant to their background
- Mix of specific and broader searches

Return ONLY a JSON array of 30 query strings, no other text:
["query 1", "query 2", ...]"""

        success, response = run_claude(prompt, timeout=180)

        if not success:
            print(f"Failed to generate queries: {response}")
            return

        try:
            json_str = extract_json_from_response(response)
            queries = json.loads(json_str)

            if not isinstance(queries, list):
                print("Invalid response format from Claude.")
                return

            self.user.query_handler.save(queries)
            print(f"Created {len(queries)} search queries.")

        except json.JSONDecodeError:
            print("Could not parse Claude's response as JSON.")

    def user_info_menu(self):
        """Show user info and provide edit options."""
        while True:
            clear_screen()
            self.display_user_info()

            action = inquirer.select(
                message="What would you like to do?",
                choices=[
                    {"name": "Edit name", "value": self.configure_name},
                    {"name": "Edit email", "value": self.configure_email},
                    {"name": "Edit credentials", "value": self.configure_credentials},
                    {"name": "Edit LinkedIn", "value": self.configure_linkedin},
                    {"name": "Edit websites", "value": self.configure_websites},
                    {"name": "Edit source documents", "value": self.configure_source_documents},
                    {"name": "Edit job titles", "value": self.configure_job_titles},
                    {"name": "Edit job locations", "value": self.configure_job_locations},
                    {"name": "Edit cover letter output directory", "value": self.configure_cover_letter_output_dir},
                    {"name": "─" * 30, "value": None, "disabled": ""},
                    {"name": "Refresh source documents", "value": self.refresh_source_documents},
                    {"name": "Refresh online presence", "value": self.refresh_online_presence},
                    {"name": "✨ Generate comprehensive summary", "value": self.generate_comprehensive_summary},
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

            action = inquirer.select(
                message="What would you like to do?",
                choices=[
                    {"name": f"Run search ({num_queries} queries)", "value": "search"},
                    {"name": "Generate new queries", "value": "generate"},
                    {"name": "← Back to main menu", "value": "back"},
                ],
            ).execute()

            if action == "back":
                return
            elif action == "generate":
                self.create_search_queries()
            elif action == "search":
                fetch_desc = inquirer.confirm(
                    message="Fetch full job descriptions? (slower but more complete)",
                    default=True
                ).execute()
                search(self.user, fetch_descriptions=fetch_desc)
                print()
  
    def jobs_menu(self):
        """View and manage found jobs."""
        while True:
            clear_screen()
            if not len(self.user.job_handler):
                print_header("Jobs")
                print(f"  {Colors.DIM}No jobs found yet.{Colors.RESET}")
                print(f"  {Colors.DIM}Use 'Search for Jobs' to find opportunities.{Colors.RESET}\n")
                return

            print_header("Jobs")
            print(f"  {Colors.GREEN}✓ {self.user.job_handler.number_applied} applied{Colors.RESET}  •  {Colors.YELLOW}○ {self.user.job_handler.number_not_applied} pending{Colors.RESET}  •  {Colors.DIM}{len(self.user.job_handler)} total{Colors.RESET}\n")

            # Display jobs as cards
            for i, job in enumerate(self.user.job_handler, 1):
                display_job_card(job, i)

            # Build choices
            job_choices = [{"name": f"{j.company} - {j.title}", "value": j.id} for j in self.user.job_handler]
            job_choices.append({"name": "─" * 30, "value": None, "disabled": ""})
            job_choices.append({"name": "← Back to main menu", "value": "back"})

            action = inquirer.select(
                message="Select a job to view details:",
                choices=job_choices,
            ).execute()

            if action == "back" or action is None:
                break

            # Show job detail
            JobOptions(user=self.user, job_id=action).menu()
    
    def main_menu(self):
        """Main application menu."""
        
                
        if self.user.is_new_user():
            self.first_time_setup()
            
        while True:
            clear_screen()
            print(ASCII_ART_JOBSEARCH)
            
            print_header(f"Welcome {self.user.name}")

            action = inquirer.select(
                message="Select an option:",
                choices=[
                    {"name": "View/Edit User Info", "value": "user"},
                    {"name": "Search for Jobs", "value": "search"},
                    {"name": "View Jobs", "value": "jobs"},
                    {"name": "Settings", "value": "settings"},
                    {"name": "Exit", "value": "exit"},
                ],
            ).execute()
            
            if action == "exit":
                print(f"\n{Colors.DIM}Goodbye!{Colors.RESET}\n")
                break
            elif action == "user":
                self.user_info_menu()
            elif action == "search":
                self.search_menu()
            elif action == "jobs":
                self.jobs_menu()
            elif action == "settings":
                print(f"\n{Colors.DIM}Settings coming soon...{Colors.RESET}\n")
