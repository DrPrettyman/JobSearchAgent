"""Main CLI for JobSearch application."""

from InquirerPy import inquirer

from data_handlers import USER
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
)


def display_user_info():
    """Display user information in a formatted view."""
    print_header("User Profile")

    # Basic Info
    print_section("Basic Information")
    print_field("Name", USER.name_with_credentials if USER.name else "")
    print_field("Email", USER.email)
    print_field("LinkedIn", USER.linkedin_url if USER.linkedin_extension else "")
    print()

    # Websites
    if USER.websites:
        print_section("Websites")
        for site in USER.websites:
            print(f"  {Colors.GREEN}•{Colors.RESET} {site}")
        print()

    # Job Preferences
    print_section("Job Preferences")
    print_list("Desired Titles", USER.desired_job_titles)
    print()
    print_list("Desired Locations", USER.desired_job_locations)
    print()

    # Source Documents
    if USER.source_document_paths:
        print_section("Source Documents")
        for path in USER.source_document_paths:
            print(f"  {Colors.GREEN}•{Colors.RESET} {path}")
        if USER.source_document_summary:
            print(f"\n  {Colors.DIM}Summary:{Colors.RESET}")
            print(f"  {USER.source_document_summary}")
        print()

    # Online Presence
    if USER.online_presence:
        print_section("Online Presence")
        for entry in USER.online_presence:
            site = entry.get("site", "Unknown")
            time_fetched = entry.get("time_fetched", "")[:10]  # Just date
            content_len = len(entry.get("content", ""))
            print(f"  {Colors.GREEN}•{Colors.RESET} {site}")
            print(f"    {Colors.DIM}Fetched: {time_fetched} ({content_len} chars){Colors.RESET}")
        if USER.online_presence_summary:
            print(f"\n  {Colors.DIM}Summary:{Colors.RESET}")
            print(f"  {USER.online_presence_summary}")
        print()


def user_info_menu():
    """Show user info and provide edit options."""
    while True:
        display_user_info()

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
            configure_name()
        elif action == "email":
            configure_email()
        elif action == "credentials":
            configure_credentials()
        elif action == "linkedin":
            configure_linkedin()
        elif action == "websites":
            configure_websites()
        elif action == "titles":
            configure_job_titles()
        elif action == "locations":
            configure_job_locations()
        elif action == "documents":
            configure_source_documents()
        elif action == "refresh_docs":
            refresh_source_documents()
        elif action == "refresh_online":
            refresh_online_presence()


def main_menu():
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
            user_info_menu()
        elif action == "search":
            print(f"\n{Colors.DIM}Search functionality coming soon...{Colors.RESET}\n")
        elif action == "jobs":
            print(f"\n{Colors.DIM}Jobs view coming soon...{Colors.RESET}\n")
        elif action == "cover":
            print(f"\n{Colors.DIM}Cover letter generation coming soon...{Colors.RESET}\n")
        elif action == "settings":
            print(f"\n{Colors.DIM}Settings coming soon...{Colors.RESET}\n")


def main():
    main_menu()


if __name__ == "__main__":
    main()
