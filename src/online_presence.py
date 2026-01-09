"""Functions to fetch online presence information from LinkedIn, GitHub, and other websites."""

import json
import urllib.request

from utils import run_claude, scrape, extract_url_slug
from data_handlers.utils import datetime_iso


def fetch_linkedin_profile(linkedin_url: str) -> str:
    """Fetch and extract professional info from a LinkedIn profile using Claude WebFetch.

    Args:
        linkedin_url: Full LinkedIn profile URL

    Returns:
        Extracted professional information as a string, or empty string on failure
    """
    prompt = f"""Fetch and analyze this LinkedIn profile: {linkedin_url}

Extract the following professional information:
- Name and headline/title
- Current and past work experience (company, role, duration)
- Education
- Skills
- Summary/About section
- Any notable achievements or certifications

Return the information in a clean, readable format. If you cannot access the profile, return exactly: NONE"""

    success, response = run_claude(
        prompt,
        timeout=180,
        tools=["WebFetch"]
    )

    if not success:
        print(f"  LinkedIn fetch failed: {response}")
        return ""

    response = response.strip()
    if response == "NONE" or len(response) < 50:
        return ""

    return response


def fetch_github_profile(github_url: str) -> str:
    """Fetch GitHub profile info via API and summarize with Claude.

    Args:
        github_url: GitHub profile URL or username

    Returns:
        Summary of GitHub profile as a string, or empty string on failure
    """
    username = extract_url_slug(github_url)
    if not username:
        return ""

    headers = {
        'User-Agent': 'JobSearch-App/1.0',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Fetch user profile
    try:
        user_req = urllib.request.Request(
            f"https://api.github.com/users/{username}",
            headers=headers
        )
        user_response = urllib.request.urlopen(user_req, timeout=30)
        user_data = json.loads(user_response.read().decode('utf-8'))
    except Exception as e:
        print(f"  Could not fetch GitHub user: {e}")
        return ""

    # Fetch repos
    repos_data = []
    try:
        repos_req = urllib.request.Request(
            f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10",
            headers=headers
        )
        repos_response = urllib.request.urlopen(repos_req, timeout=30)
        repos_data = json.loads(repos_response.read().decode('utf-8'))
    except Exception as e:
        print(f"  Could not fetch GitHub repos: {e}")

    # Prepare data for Claude
    profile_info = {
        "name": user_data.get("name"),
        "login": user_data.get("login"),
        "bio": user_data.get("bio"),
        "company": user_data.get("company"),
        "location": user_data.get("location"),
        "blog": user_data.get("blog"),
        "public_repos": user_data.get("public_repos"),
        "followers": user_data.get("followers"),
        "following": user_data.get("following"),
        "created_at": user_data.get("created_at")
    }

    repos_info = [{
        "name": repo.get("name"),
        "description": repo.get("description"),
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count"),
        "forks": repo.get("forks_count"),
        "updated_at": repo.get("updated_at")
    } for repo in repos_data[:10]]

    prompt = f"""Summarize this GitHub developer profile for a job application context.

Profile:
{json.dumps(profile_info, indent=2)}

Recent Repositories:
{json.dumps(repos_info, indent=2)}

Create a professional summary highlighting:
- Developer's focus areas and expertise
- Most notable or relevant projects
- Languages and technologies used
- Any indicators of experience level or contributions

Keep the summary concise but informative (3-5 paragraphs)."""

    success, response = run_claude(prompt, timeout=60)

    if not success:
        # Fallback: return raw profile data
        return f"GitHub: {username}\nBio: {profile_info.get('bio', 'N/A')}\nPublic repos: {profile_info.get('public_repos', 0)}"

    return response.strip()


def fetch_website_content(url: str) -> str:
    """Scrape a website and extract relevant professional information.

    Args:
        url: Website URL to scrape

    Returns:
        Extracted professional information as a string, or empty string on failure
    """
    try:
        html_text = scrape(url)
    except Exception as e:
        print(f"  Could not scrape {url}: {e}")
        return ""

    if not html_text or len(html_text) < 100:
        return ""

    prompt = f"""Extract professional/career-relevant information from this website content.

Look for:
- About/bio information
- Work experience or portfolio
- Skills and expertise
- Projects or accomplishments
- Contact information
- Any professional credentials or certifications

Return the extracted information in a clean, readable format.
If you cannot find relevant professional information, return exactly: NONE

Website content:
{html_text}"""

    success, response = run_claude(prompt, timeout=60)

    if not success:
        return ""

    response = response.strip()
    if response == "NONE" or len(response) < 50:
        return ""

    return response


def fetch_online_presence(urls: list[str]) -> list[dict]:
    """Fetch online presence from a list of URLs.

    Automatically detects LinkedIn, GitHub, or generic websites.

    Args:
        urls: List of URLs to fetch

    Returns:
        List of dicts with keys: site, time_fetched, content
    """
    results = []

    for url in urls:
        url_lower = url.lower()

        if "linkedin.com" in url_lower:
            print(f"Fetching LinkedIn profile: /in/{extract_url_slug(url)}")
            content = fetch_linkedin_profile(url)
        elif "github.com" in url_lower:
            print(f"Fetching GitHub profile: {url}")
            content = fetch_github_profile(url)
        else:
            print(f"Fetching website: {url}")
            content = fetch_website_content(url)

        if content:
            results.append({
                "site": url,
                "time_fetched": datetime_iso(),
                "content": content
            })
            print(f"  Got {len(content)} chars")
        else:
            print("  No content extracted")

    return results
