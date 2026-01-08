"""CLI menu functions for JobSearch application."""

from InquirerPy import inquirer

from data_handlers import User
from cli_utils import Colors, print_header, print_section, print_field, print_list, hyperlink
from configure import (
    configure_name,
    configure_email,
    configure_credentials,
    configure_linkedin,
    configure_websites,
    configure_source_documents,
    configure_job_titles,
    configure_job_locations,
    refresh_source_documents,
    refresh_online_presence,
    create_search_queries,
)
from search_jobs import search


def display_user_info(user: User, skip: bool = False):
    """Display user information in a formatted view."""
    if skip:
        return

    print_header("User Profile")

    # Basic Info
    print_section("Basic Information")
    print_field("Name", user.name_with_credentials if user.name else "")
    print_field("Email", user.email)
    print_field("LinkedIn", user.linkedin_url if user.linkedin_extension else "")
    print()

    # Websites
    if user.websites:
        print_section("Websites")
        for site in user.websites:
            print(f"  {Colors.GREEN}•{Colors.RESET} {site}")
        print()

    # Job Preferences
    print_section("Job Preferences")
    print_list("Desired Titles", user.desired_job_titles)
    print()
    print_list("Desired Locations", user.desired_job_locations)
    print()

    # Source Documents
    if user.source_document_paths:
        print_section("Source Documents")
        for path in user.source_document_paths:
            print(f"  {Colors.GREEN}•{Colors.RESET} {path}")
        if user.source_document_summary:
            print(f"\n  {Colors.DIM}Summary:{Colors.RESET}")
            print(f"  {user.source_document_summary}")
        print()

    # Online Presence
    if user.online_presence:
        print_section("Online Presence")
        for entry in user.online_presence:
            site = entry.get("site", "Unknown")
            time_fetched = entry.get("time_fetched", "")[:10]  # Just date
            content_len = len(entry.get("content", ""))
            print(f"  {Colors.GREEN}•{Colors.RESET} {site}")
            print(f"    {Colors.DIM}Fetched: {time_fetched} ({content_len} chars){Colors.RESET}")
        if user.online_presence_summary:
            print(f"\n  {Colors.DIM}Summary:{Colors.RESET}")
            print(f"  {user.online_presence_summary}")
        print()


def user_info_menu(user: User, skip_first_display: bool = False):
    """Show user info and provide edit options."""
    while True:
        display_user_info(user, skip=skip_first_display)
        skip_first_display = False

        action = inquirer.select(
            message="What would you like to do?",
            choices=[
                {"name": "Edit name", "value": "name"},
                {"name": "Edit email", "value": "email"},
                {"name": "Edit credentials", "value": "credentials"},
                {"name": "Edit LinkedIn", "value": "linkedin"},
                {"name": "Edit websites", "value": "websites"},
                {"name": "Edit job titles", "value": "titles"},
                {"name": "Edit job locations", "value": "locations"},
                {"name": "Edit source documents", "value": "documents"},
                {"name": "Refresh source documents", "value": "refresh_docs"},
                {"name": "Refresh online presence", "value": "refresh_online"},
                {"name": "← Back to main menu", "value": "back"},
            ],
        ).execute()

        if action == "back":
            break
        elif action == "name":
            configure_name(user)
        elif action == "email":
            configure_email(user)
        elif action == "credentials":
            configure_credentials(user)
        elif action == "linkedin":
            configure_linkedin(user)
        elif action == "websites":
            configure_websites(user)
        elif action == "titles":
            configure_job_titles(user)
        elif action == "locations":
            configure_job_locations(user)
        elif action == "documents":
            configure_source_documents(user)
        elif action == "refresh_docs":
            refresh_source_documents(user)
        elif action == "refresh_online":
            refresh_online_presence(user)


def search_menu(user: User):
    """Search for jobs menu."""
    print_header("Search for Jobs")

    num_queries = len(user.query_handler)
    num_jobs = len(user.job_handler)

    print(f"  {Colors.DIM}Search queries: {num_queries}{Colors.RESET}")
    print(f"  {Colors.DIM}Jobs found: {num_jobs}{Colors.RESET}\n")

    if num_queries == 0:
        print(f"{Colors.YELLOW}No search queries configured.{Colors.RESET}")
        generate = inquirer.confirm(
            message="Would you like to generate search queries now?",
            default=True
        ).execute()
        if generate:
            create_search_queries(user)
            num_queries = len(user.query_handler)
            if num_queries == 0:
                print(f"\n{Colors.DIM}No queries generated. Configure job titles and locations first.{Colors.RESET}\n")
                return
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
        create_search_queries(user)
    elif action == "search":
        fetch_desc = inquirer.confirm(
            message="Fetch full job descriptions? (slower but more complete)",
            default=True
        ).execute()
        search(user, fetch_descriptions=fetch_desc)
        print()


def display_job_card(job, index: int = None):
    """Display a single job as a beautiful card."""
    # Status indicator
    if job.applied:
        status = f"{Colors.GREEN}✓ Applied{Colors.RESET}"
    else:
        status = f"{Colors.YELLOW}○ Not applied{Colors.RESET}"

    # Index prefix if provided
    prefix = f"{Colors.DIM}[{index}]{Colors.RESET} " if index is not None else ""

    # Company and title line
    print(f"  {prefix}{Colors.BOLD}{job.company}{Colors.RESET}")
    print(f"      {Colors.CYAN}{job.title}{Colors.RESET}  {status}")

    # Location and date
    location = job.location or "Location not specified"
    date = job.date_found[:10] if job.date_found else "Unknown date"
    print(f"      {Colors.DIM}📍 {location}  •  📅 {date}{Colors.RESET}")

    # Clickable apply link
    if job.link:
        link_text = hyperlink(job.link, "Apply →")
        print(f"      {Colors.BLUE}{link_text}{Colors.RESET}")

    print()


def display_job_detail(job):
    """Display detailed view of a single job."""
    print_header(f"{job.company}")

    # Status badge
    if job.applied:
        print(f"  {Colors.GREEN}━━━ ✓ APPLIED ━━━{Colors.RESET}\n")
    else:
        print(f"  {Colors.YELLOW}━━━ ○ NOT YET APPLIED ━━━{Colors.RESET}\n")

    # Main info
    print_section("Position Details")
    print_field("Title", job.title)
    print_field("Location", job.location)
    print_field("Found", job.date_found[:10] if job.date_found else "")
    if job.addressee:
        print_field("Hiring Manager", job.addressee)
    print()

    # Apply link (prominent)
    if job.link:
        print_section("Apply")
        link = hyperlink(job.link, job.link)
        print(f"  {Colors.BLUE}{Colors.BOLD}{link}{Colors.RESET}")
        print()

    # Description
    if job.description:
        print_section("Summary")
        # Word wrap the description
        words = job.description.split()
        line = "  "
        for word in words:
            if len(line) + len(word) > 78:
                print(line)
                line = "  "
            line += word + " "
        if line.strip():
            print(line)
        print()

    # Full description (truncated preview)
    if job.full_description:
        print_section("Full Description")
        preview = job.full_description[:500]
        if len(job.full_description) > 500:
            preview += "..."
        # Word wrap
        words = preview.split()
        line = "  "
        for word in words:
            if len(line) + len(word) > 78:
                print(line)
                line = "  "
            line += word + " "
        if line.strip():
            print(line)
        print(f"\n  {Colors.DIM}({len(job.full_description)} characters total){Colors.RESET}")
        print()


def jobs_menu(user: User):
    """View and manage found jobs."""
    while True:
        jobs = list(user.job_handler)

        if not jobs:
            print_header("Jobs")
            print(f"  {Colors.DIM}No jobs found yet.{Colors.RESET}")
            print(f"  {Colors.DIM}Use 'Search for Jobs' to find opportunities.{Colors.RESET}\n")
            return

        # Stats
        applied_count = sum(1 for j in jobs if j.applied)
        pending_count = len(jobs) - applied_count

        print_header("Jobs")
        print(f"  {Colors.GREEN}✓ {applied_count} applied{Colors.RESET}  •  {Colors.YELLOW}○ {pending_count} pending{Colors.RESET}  •  {Colors.DIM}{len(jobs)} total{Colors.RESET}\n")

        # Display jobs as cards
        for i, job in enumerate(jobs, 1):
            display_job_card(job, i)

        # Build choices
        job_choices = [
            {"name": f"{j.company} - {j.title}", "value": j.id}
            for j in jobs
        ]
        job_choices.append({"name": "─" * 30, "value": None, "disabled": ""})
        job_choices.append({"name": "← Back to main menu", "value": "back"})

        action = inquirer.select(
            message="Select a job to view details:",
            choices=job_choices,
        ).execute()

        if action == "back" or action is None:
            break

        # Show job detail
        job = user.job_handler.get(action)
        if job:
            job_detail_menu(user, job)


def job_detail_menu(user: User, job):
    """View and manage a single job."""
    while True:
        display_job_detail(job)

        choices = []
        if not job.applied:
            choices.append({"name": "✓ Mark as applied", "value": "apply"})
        else:
            choices.append({"name": "○ Mark as not applied", "value": "unapply"})

        if job.link:
            choices.append({"name": "🔗 Open job link", "value": "open"})

        choices.append({"name": "← Back to jobs list", "value": "back"})

        action = inquirer.select(
            message="What would you like to do?",
            choices=choices,
        ).execute()

        if action == "back":
            break
        elif action == "apply":
            job.applied = True
            user.job_handler.save()
            print(f"\n{Colors.GREEN}✓ Marked as applied!{Colors.RESET}\n")
        elif action == "unapply":
            job.applied = False
            user.job_handler.save()
            print(f"\n{Colors.YELLOW}○ Marked as not applied.{Colors.RESET}\n")
        elif action == "open":
            import webbrowser
            webbrowser.open(job.link)
            print(f"\n{Colors.DIM}Opening in browser...{Colors.RESET}\n")


def main_menu(user: User):
    """Main application menu."""
    while True:
        print_header("JobSearch")

        action = inquirer.select(
            message="Select an option:",
            choices=[
                {"name": "View/Edit User Info", "value": "user"},
                {"name": "Search for Jobs", "value": "search"},
                {"name": "View Jobs", "value": "jobs"},
                {"name": "Generate Cover Letters", "value": "cover"},
                {"name": "Settings", "value": "settings"},
                {"name": "Exit", "value": "exit"},
            ],
        ).execute()

        if action == "exit":
            print(f"\n{Colors.DIM}Goodbye!{Colors.RESET}\n")
            break
        elif action == "user":
            user_info_menu(user)
        elif action == "search":
            search_menu(user)
        elif action == "jobs":
            jobs_menu(user)
        elif action == "cover":
            print(f"\n{Colors.DIM}Cover letter generation coming soon...{Colors.RESET}\n")
        elif action == "settings":
            print(f"\n{Colors.DIM}Settings coming soon...{Colors.RESET}\n")
