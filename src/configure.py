import json
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.validator import PathValidator

from utils import run_claude, extract_url_slug, summarize_source_documents, summarize_online_presence
from online_presence import fetch_online_presence
from data_handlers import User


def configure_name(user: User):
    """Configure user's name."""
    user.name = inquirer.text(
        message="Your name:",
        default=user.name,
    ).execute()
    user.save()


def configure_email(user: User):
    """Configure user's email."""
    user.email = inquirer.text(
        message="Your email:",
        default=user.email,
    ).execute()
    user.save()


# Ordered by precedence (most prestigious first)
CREDENTIAL_OPTIONS = [
    "PhD",
    "MD",
    "JD",
    "EdD",
    "DBA",
    "MBA",
    "MS",
    "MA",
    "MEng",
    "MFA",
    "MPH",
    "CPA",
    "CFA",
    "PMP",
    "PE",
]


def configure_credentials(user: User):
    """Configure user's credentials/titles."""
    current = user.credentials

    choices = [
        {"name": cred, "value": cred, "enabled": cred in current}
        for cred in CREDENTIAL_OPTIONS
    ]

    selected = inquirer.checkbox(
        message="Select your credentials (in order of precedence):",
        choices=choices,
    ).execute()

    user.credentials = selected
    user.save()


def configure_linkedin(user: User):
    """Configure LinkedIn profile."""
    current = user.linkedin_extension
    display = f"(current: {current})" if current else ""

    value = inquirer.text(
        message=f"LinkedIn URL or username {display}:",
        default=current,
    ).execute()

    if value:
        user.linkedin_extension = extract_url_slug(value)
    else:
        user.linkedin_extension = ""
    user.save()


def configure_websites(user: User):
    """Configure personal websites/portfolios."""
    while True:
        sites = user.websites
        if sites:
            print("\nCurrent websites:")
            for i, s in enumerate(sites, 1):
                print(f"  {i}. {s}")
        else:
            print("\nNo websites configured yet.")

        choices = [{"name": "Add a website", "value": "add"}]
        if sites:
            choices.append({"name": "Remove a website", "value": "remove"})
        choices.append({"name": "Done", "value": "done"})

        action = inquirer.select(
            message="Websites:",
            choices=choices,
        ).execute()

        if action == "done":
            break
        elif action == "add":
            url = inquirer.text(message="Enter website URL:").execute()
            if url:
                user.add_website(url)
        elif action == "remove":
            to_remove = inquirer.select(
                message="Select website to remove:",
                choices=[{"name": s, "value": s} for s in sites] + [{"name": "Cancel", "value": None}],
            ).execute()
            if to_remove:
                user.remove_website(to_remove)

    # Check for LinkedIn URLs in websites
    linkedin_urls = [s for s in user.websites if "linkedin.com" in s.lower()]
    for url in linkedin_urls:
        parsed = extract_url_slug(url)
        if user.linkedin_extension:
            # Already have LinkedIn configured, remove duplicate
            user.remove_website(url)
            print("Removed LinkedIn URL from websites (already configured)")
        else:
            # No LinkedIn configured, move it there
            user.linkedin_extension = parsed
            user.remove_website(url)
            print(f"Moved LinkedIn URL to dedicated field: {parsed}")

    user.save()


def configure_source_documents(user: User):
    """Configure source document paths."""
    while True:
        paths = user._source_document_paths
        if paths:
            print("\nCurrent paths:")
            for i, p in enumerate(paths, 1):
                print(f"  {i}. {p}")
        else:
            print("\nNo source documents configured yet.")

        action = inquirer.select(
            message="What would you like to do?",
            choices=[
                {"name": "Add a file or folder", "value": "add"},
                {"name": "Remove a path", "value": "remove"},
                {"name": "Clear all paths", "value": "clear"},
                {"name": "Done", "value": "done"},
            ],
        ).execute()

        if action == "done":
            break
        elif action == "clear":
            user._source_document_paths.clear()
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
                user.remove_source_document_path(to_remove)
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

            user.add_source_document_path(selected_path)
            print(f"Added: {selected_path}")

    user.save()
    user.update_combined_docs()

    if user.combined_source_documents:
        print("Generating summary of source documents...")
        summary = summarize_source_documents(user.combined_source_documents)
        if summary:
            user.source_document_summary = summary
            user.save()
            print("Summary generated.")
        else:
            print("Could not generate summary.")


def refresh_source_documents(user: User):
    """Re-read source documents and regenerate summary."""
    if not user.source_document_paths:
        print("No source documents configured.")
        return

    print("Re-reading source documents...")
    user.update_combined_docs()

    if user.combined_source_documents:
        print("Generating summary...")
        summary = summarize_source_documents(user.combined_source_documents)
        if summary:
            user.source_document_summary = summary
            user.save()
            print("Summary updated.")
        else:
            print("Could not generate summary.")
    else:
        print("No content found in source documents.")


def refresh_online_presence(user: User):
    """Fetch online presence and regenerate summary."""
    urls = []
    if user.linkedin_url:
        urls.append(user.linkedin_url)
    urls.extend(user.websites)

    if not urls:
        print("No online presence URLs configured.")
        return

    print("Fetching online presence...")
    results = fetch_online_presence(urls)

    user.clear_online_presence()
    for entry in results:
        user.add_online_presence(entry["site"], entry["content"], entry["time_fetched"])

    if user.online_presence:
        print("Generating summary...")
        summary = summarize_online_presence(user.online_presence)
        if summary:
            user.online_presence_summary = summary
        else:
            print("Could not generate summary.")

    user.save()
    print(f"Fetched {len(results)} profiles.")


def configure_job_titles(user: User):
    """Configure desired job titles."""
    while True:
        titles = user.desired_job_titles
        print(f"\nCurrent job titles: {titles}")

        choices = [{"name": "Add a title", "value": "add"}]
        if titles:
            choices.append({"name": "Remove a title", "value": "remove"})
        choices.append({"name": "Done", "value": "done"})

        action = inquirer.select(
            message="Job titles:",
            choices=choices,
        ).execute()

        if action == "done":
            break
        elif action == "add":
            new_title = inquirer.text(message="Enter job title:").execute()
            if new_title:
                user.add_desired_job_title(new_title)
        elif action == "remove":
            to_remove = inquirer.select(
                message="Select title to remove:",
                choices=[{"name": t, "value": t} for t in titles] + [{"name": "Cancel", "value": None}],
            ).execute()
            if to_remove:
                user.remove_desired_job_title(to_remove)

    user.save()


def configure_job_locations(user: User):
    """Configure desired job locations."""
    while True:
        locations = user.desired_job_locations
        print(f"\nCurrent job locations: {locations}")

        choices = [{"name": "Add a location", "value": "add"}]
        if locations:
            choices.append({"name": "Remove a location", "value": "remove"})
        choices.append({"name": "Done", "value": "done"})

        action = inquirer.select(
            message="Job locations:",
            choices=choices,
        ).execute()

        if action == "done":
            break
        elif action == "add":
            new_loc = inquirer.text(message="Enter job location:").execute()
            if new_loc:
                user.add_desired_job_location(new_loc)
        elif action == "remove":
            to_remove = inquirer.select(
                message="Select location to remove:",
                choices=[{"name": loc, "value": loc} for loc in locations] + [{"name": "Cancel", "value": None}],
            ).execute()
            if to_remove:
                user.remove_desired_job_location(to_remove)

    user.save()


def suggest_from_documents(user: User):
    """Use Claude to suggest job titles and locations from source documents."""
    if not user.source_document_paths:
        print("No source documents configured. Add documents first.")
        return

    combined_docs = user._combined_source_documents
    if not combined_docs:
        user.update_combined_docs()
        combined_docs = user._combined_source_documents

    if not combined_docs:
        print("Could not read any source documents.")
        return

    print("Analyzing your documents to suggest job titles and locations...")

    prompt = f"""Analyze the following CV/resume documents and suggest:
1. A list of 5-10 job titles this person would be suitable for
2. A list of 3-5 preferred job locations based on any hints in the documents. Example locations ["Manchester", "UK, Remote", "Europe, Remote"]

Respond ONLY with valid JSON in this exact format, no other text:
{{"job_titles": ["Title 1", "Title 2"], "job_locations": ["Location 1", "Location 2"]}}

Documents:
{combined_docs}"""

    success, response = run_claude(prompt, timeout=180)

    if not success:
        print(f"Claude analysis failed: {response}")
        return

    try:
        response = response.strip()
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()

        suggestions = json.loads(response)
        suggested_titles = suggestions.get("job_titles", [])
        suggested_locations = suggestions.get("job_locations", [])

        if suggested_titles:
            selected_titles = inquirer.checkbox(
                message="Select job titles to add:",
                choices=[{"name": t, "value": t, "enabled": True} for t in suggested_titles],
            ).execute()
            for title in selected_titles:
                user.add_desired_job_title(title)

        if suggested_locations:
            selected_locations = inquirer.checkbox(
                message="Select job locations to add:",
                choices=[{"name": loc, "value": loc, "enabled": True} for loc in suggested_locations],
            ).execute()
            for loc in selected_locations:
                user.add_desired_job_location(loc)

        user.save()

    except json.JSONDecodeError:
        print("Could not parse Claude's response.")


def configure_all(user: User):
    """Run full configuration flow."""
    print("=== Configure User Info ===\n")
    configure_name(user)
    configure_email(user)
    configure_credentials(user)
    configure_linkedin(user)
    configure_websites(user)

    print("\n=== Configure Source Documents ===")
    configure_source_documents(user)

    print("\n=== Configure Job Preferences ===")
    if user.source_document_paths:
        use_ai = inquirer.confirm(
            message="Would you like AI to suggest job titles and locations from your documents?",
            default=True
        ).execute()
        if use_ai:
            suggest_from_documents(user)

    configure_job_titles(user)
    configure_job_locations(user)

    print("\nConfiguration complete.")


def create_search_queries(user: User):
    """Create search queries from the user's information."""

    if not user.desired_job_titles:
        print("No job titles configured. Run configure_job_titles() first.")
        return

    if not user.desired_job_locations:
        print("No job locations configured. Run configure_job_locations() first.")
        return

    print("Generating search queries...")

    # Truncate docs to avoid token limits
    docs_summary = user._combined_source_documents[:4000] if user._combined_source_documents else ""

    prompt = f"""Based on this job seeker's profile, create 30 effective job search queries.

Job titles of interest: {user.desired_job_titles}
Preferred locations: {user.desired_job_locations}

Background summary:
{docs_summary}

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
        response = response.strip()
        # Handle markdown code blocks
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()

        queries = json.loads(response)

        if not isinstance(queries, list):
            print("Invalid response format from Claude.")
            return

        user.query_handler.save(queries)
        print(f"Created {len(queries)} search queries.")

    except json.JSONDecodeError:
        print("Could not parse Claude's response as JSON.")

    