#!/usr/bin/env python3
"""
Automate job application workflow by chaining Claude CLI calls.

Usage:
    python automate_jobs.py                    # Run full pipeline
    python automate_jobs.py --phase scrape     # Only scrape descriptions
    python automate_jobs.py --phase topics     # Only generate topics
    python automate_jobs.py --phase letters    # Only write cover letters
    python automate_jobs.py --phase review     # Only review cover letters
    python automate_jobs.py --company Veriff   # Process specific company only
    python automate_jobs.py --dry-run          # Show what would be done
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
JOBS_FILE = SCRIPT_DIR / "jobs.json"
INSTRUCTIONS_FILE = SCRIPT_DIR / "claude-instructions.md"
CV_FILE = SCRIPT_DIR.parent / "public" / "cv" / "two_page" / "JPrettymanCV.tex"


def load_jobs() -> list:
    """Load jobs from jobs.json."""
    with open(JOBS_FILE, "r") as f:
        return json.load(f)


def save_jobs(jobs: list) -> None:
    """Save jobs to jobs.json."""
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=4)


def run_claude(prompt: str, timeout: int = 120) -> tuple[bool, str]:
    """Run Claude CLI with a prompt. Returns (success, output)."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Timeout expired"
    except Exception as e:
        return False, str(e)


def scrape_page(url: str) -> tuple[bool, str]:
    """Scrape webpage. Returns (success, content)."""
    try:
        result = subprocess.run(
            ["python3", str(SCRIPT_DIR / "scrape_job.py"), url],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except Exception as e:
        return False, str(e)


def phase_scrape(jobs: list, company_filter: str = None, dry_run: bool = False) -> list:
    """
    Phase 4: Scrape full job descriptions for jobs that need them.
    Updates jobs with full_description field.
    """
    print("\n" + "=" * 60)
    print("PHASE: SCRAPE JOB DESCRIPTIONS")
    print("=" * 60)

    jobs_to_scrape = [
        j for j in jobs
        if j.get("link")
        and not j.get("full_description")
        and not j.get("applied")  # Skip already-applied jobs
        and (not company_filter or j.get("company", "").lower() == company_filter.lower())
    ]

    if not jobs_to_scrape:
        print("No jobs need scraping.")
        return jobs

    print(f"Found {len(jobs_to_scrape)} jobs to scrape.\n")

    for job in jobs_to_scrape:
        company = job.get("company", "Unknown")
        url = job.get("link")
        print(f"Scraping: {company}")
        print(f"  URL: {url}")

        if dry_run:
            print("  [DRY RUN] Would scrape and update description")
            continue

        success, content = scrape_job_description(url)

        if success and len(content.strip()) > 100:
            # Use Claude to extract the relevant job description from the scraped content
            prompt = f"""Extract ONLY the job description from this scraped webpage content.
Remove navigation, headers, footers, and other irrelevant content.
Return just the job posting text (responsibilities, requirements, about the company, etc.)

Company: {company}
URL: {url}

Scraped content:
{content[:15000]}

Return the cleaned job description text only, no commentary."""

            print("  Calling Claude to clean scraped content...")
            claude_success, cleaned = run_claude(prompt, timeout=60)

            if claude_success and cleaned.strip():
                # Find and update the job in the original list
                for j in jobs:
                    if j.get("company") == company and j.get("link") == url:
                        j["description"] = cleaned.strip()
                        j["full_description"] = True
                        print(f"  ✓ Updated description ({len(cleaned)} chars)")
                        break
            else:
                print(f"  ✗ Claude failed to clean content")
                for j in jobs:
                    if j.get("company") == company:
                        j["full_description"] = False
        else:
            print(f"  ✗ Scraping failed: {content[:100] if content else 'No content'}")
            for j in jobs:
                if j.get("company") == company:
                    j["full_description"] = False

    if not dry_run:
        save_jobs(jobs)
        print("\nSaved updated jobs.json")

    return jobs


def phase_topics(jobs: list, company_filter: str = None, dry_run: bool = False) -> list:
    """
    Phase 5: Create cover letter topics for jobs that have full descriptions.
    """
    print("\n" + "=" * 60)
    print("PHASE: CREATE COVER LETTER TOPICS")
    print("=" * 60)

    jobs_to_process = [
        j for j in jobs
        if j.get("full_description") == True
        and not j.get("cover_letter_topics")
        and not j.get("applied")
        and (not company_filter or j.get("company", "").lower() == company_filter.lower())
    ]

    if not jobs_to_process:
        print("No jobs need cover letter topics.")
        return jobs

    # Load instructions for context
    instructions = ""
    if INSTRUCTIONS_FILE.exists():
        instructions = INSTRUCTIONS_FILE.read_text()

    print(f"Found {len(jobs_to_process)} jobs needing topics.\n")

    for job in jobs_to_process:
        company = job.get("company", "Unknown")
        title = job.get("title", "Unknown")
        description = job.get("description", "")

        print(f"Creating topics for: {company} - {title}")

        if dry_run:
            print("  [DRY RUN] Would generate cover letter topics")
            continue

        prompt = f"""Create cover letter topics for this job application.

INSTRUCTIONS:
{instructions[:3000]}

JOB:
Company: {company}
Title: {title}
Description: {description[:4000]}

Create a JSON array of topic objects, each mapping a job requirement to relevant experience.
Format: [{{"requirement": "...", "experience": "...", "metrics": "..."}}]

Return ONLY the JSON array, no other text."""

        success, output = run_claude(prompt, timeout=90)

        if success and output.strip():
            # Try to parse as JSON
            try:
                # Find JSON array in output
                start = output.find("[")
                end = output.rfind("]") + 1
                if start >= 0 and end > start:
                    topics = json.loads(output[start:end])
                    for j in jobs:
                        if j.get("company") == company:
                            j["cover_letter_topics"] = topics
                            print(f"  ✓ Created {len(topics)} topics")
                            break
                else:
                    print(f"  ✗ No JSON array found in output")
            except json.JSONDecodeError as e:
                print(f"  ✗ Failed to parse JSON: {e}")
        else:
            print(f"  ✗ Claude failed: {output[:100] if output else 'No output'}")

    if not dry_run:
        save_jobs(jobs)
        print("\nSaved updated jobs.json")

    return jobs


def phase_letters(jobs: list, company_filter: str = None, dry_run: bool = False) -> list:
    """
    Phase 6: Write cover letters for jobs that have topics but no letter yet.
    """
    print("\n" + "=" * 60)
    print("PHASE: WRITE COVER LETTERS")
    print("=" * 60)

    jobs_to_process = [
        j for j in jobs
        if j.get("cover_letter_topics")
        and not j.get("cover_letter")
        and not j.get("applied")
        and (not company_filter or j.get("company", "").lower() == company_filter.lower())
    ]

    if not jobs_to_process:
        print("No jobs need cover letters.")
        return jobs

    # Load instructions and CV for context
    instructions = ""
    if INSTRUCTIONS_FILE.exists():
        instructions = INSTRUCTIONS_FILE.read_text()

    cv_content = ""
    if CV_FILE.exists():
        cv_content = CV_FILE.read_text()

    print(f"Found {len(jobs_to_process)} jobs needing cover letters.\n")

    for job in jobs_to_process:
        company = job.get("company", "Unknown")
        title = job.get("title", "Unknown")
        description = job.get("description", "")
        topics = job.get("cover_letter_topics", [])

        print(f"Writing cover letter for: {company} - {title}")

        if dry_run:
            print("  [DRY RUN] Would write cover letter")
            continue

        prompt = f"""Write a cover letter for this job application.

COVER LETTER INSTRUCTIONS (FOLLOW STRICTLY):
{instructions[:4000]}

CV FOR ACCURATE DATES:
{cv_content[:3000]}

JOB DETAILS:
Company: {company}
Title: {title}
Description: {description[:3000]}

TOPICS TO COVER:
{json.dumps(topics, indent=2)[:2000]}

Write a 4-6 paragraph cover letter. Use contractions. No em-dashes.
Do NOT start with "I am writing to apply".
Return ONLY the cover letter body text, no salutation or signature."""

        success, output = run_claude(prompt, timeout=120)

        if success and output.strip() and len(output.strip()) > 200:
            for j in jobs:
                if j.get("company") == company:
                    j["cover_letter"] = output.strip()
                    print(f"  ✓ Written ({len(output)} chars)")
                    break
        else:
            print(f"  ✗ Claude failed: {output[:100] if output else 'No output'}")

    if not dry_run:
        save_jobs(jobs)
        print("\nSaved updated jobs.json")

    return jobs


def phase_review(jobs: list, company_filter: str = None, dry_run: bool = False) -> list:
    """
    Phase 7: Review cover letters for AI patterns and accuracy.
    """
    print("\n" + "=" * 60)
    print("PHASE: REVIEW COVER LETTERS")
    print("=" * 60)

    jobs_to_review = [
        j for j in jobs
        if j.get("cover_letter")
        and not j.get("reviewed")
        and not j.get("applied")
        and (not company_filter or j.get("company", "").lower() == company_filter.lower())
    ]

    if not jobs_to_review:
        print("No cover letters need review.")
        return jobs

    instructions = ""
    if INSTRUCTIONS_FILE.exists():
        instructions = INSTRUCTIONS_FILE.read_text()

    print(f"Found {len(jobs_to_review)} cover letters to review.\n")

    for job in jobs_to_review:
        company = job.get("company", "Unknown")
        cover_letter = job.get("cover_letter", "")

        print(f"Reviewing: {company}")

        if dry_run:
            print("  [DRY RUN] Would review cover letter")
            continue

        prompt = f"""Review this cover letter for AI writing patterns and suggest improvements.

PATTERNS TO CHECK (from instructions):
{instructions[:3000]}

COVER LETTER:
{cover_letter}

Check for:
1. Em-dashes (should use colons, commas, or periods instead)
2. Phrases like "I am writing to apply", "aligns closely with", "I would welcome"
3. Contrastive reframes ("It wasn't just X, it was Y")
4. Rule of three for rhetorical effect
5. Flattering intensifiers (fascinating, remarkable, compelling, truly, deeply)
6. Excessive transitions (Furthermore, Moreover, Indeed)
7. Same-length paragraphs

If the letter passes, respond with just: PASS
If issues found, list them briefly and provide a corrected version."""

        success, output = run_claude(prompt, timeout=90)

        if success:
            output_lower = output.strip().lower()
            if output_lower == "pass" or output_lower.startswith("pass"):
                for j in jobs:
                    if j.get("company") == company:
                        j["reviewed"] = True
                        print(f"  ✓ PASSED review")
                        break
            else:
                print(f"  ⚠ Issues found:")
                # Print first few lines of feedback
                for line in output.strip().split("\n")[:5]:
                    print(f"    {line}")

                # If Claude provided a corrected version, offer to use it
                if "corrected" in output.lower() or len(output) > len(cover_letter):
                    # Try to extract corrected letter (after "Corrected:" or similar)
                    for marker in ["Corrected version:", "Corrected:", "Here's the corrected"]:
                        if marker.lower() in output.lower():
                            idx = output.lower().find(marker.lower())
                            corrected = output[idx + len(marker):].strip()
                            if len(corrected) > 200:
                                for j in jobs:
                                    if j.get("company") == company:
                                        j["cover_letter"] = corrected
                                        j["reviewed"] = True
                                        print(f"  ✓ Auto-corrected and marked reviewed")
                                        break
                            break
        else:
            print(f"  ✗ Review failed: {output[:100] if output else 'No output'}")

    if not dry_run:
        save_jobs(jobs)
        print("\nSaved updated jobs.json")

    return jobs


def generate_pdfs():
    """Run generate_cover_letters.py to create PDFs."""
    print("\n" + "=" * 60)
    print("GENERATING PDF COVER LETTERS")
    print("=" * 60)

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "generate_cover_letters.py")],
        capture_output=False
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Automate job application workflow")
    parser.add_argument("--phase", choices=["scrape", "topics", "letters", "review", "pdfs"],
                        help="Run only a specific phase")
    parser.add_argument("--company", help="Process only a specific company")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--no-pdfs", action="store_true", help="Skip PDF generation")
    args = parser.parse_args()

    jobs = load_jobs()
    print(f"Loaded {len(jobs)} jobs from jobs.json")

    phases = {
        "scrape": phase_scrape,
        "topics": phase_topics,
        "letters": phase_letters,
        "review": phase_review,
    }

    if args.phase:
        if args.phase == "pdfs":
            generate_pdfs()
        else:
            phases[args.phase](jobs, args.company, args.dry_run)
    else:
        # Run all phases in order
        jobs = phase_scrape(jobs, args.company, args.dry_run)
        jobs = phase_topics(jobs, args.company, args.dry_run)
        jobs = phase_letters(jobs, args.company, args.dry_run)
        jobs = phase_review(jobs, args.company, args.dry_run)

        if not args.no_pdfs and not args.dry_run:
            generate_pdfs()

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
