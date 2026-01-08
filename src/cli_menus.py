"""CLI menu functions for JobSearch application."""

from InquirerPy import inquirer

from data_handlers import User
from cli_utils import Colors, print_header, print_section, print_field, print_list
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
            print(f"\n{Colors.DIM}Jobs view coming soon...{Colors.RESET}\n")
        elif action == "cover":
            print(f"\n{Colors.DIM}Cover letter generation coming soon...{Colors.RESET}\n")
        elif action == "settings":
            print(f"\n{Colors.DIM}Settings coming soon...{Colors.RESET}\n")
