"""CLI formatting utilities."""
import os

from data_handlers import Job


ASCII_ART_JOBSEARCH = """   $$$$$\           $$\        $$$$$$\                                          $$\       
   \__$$ |          $$ |      $$  __$$\                                         $$ |      
      $$ | $$$$$$\  $$$$$$$\  $$ /  \__| $$$$$$\   $$$$$$\   $$$$$$\   $$$$$$$\ $$$$$$$\  
      $$ |$$  __$$\ $$  __$$\ \$$$$$$\  $$  __$$\  \____$$\ $$  __$$\ $$  _____|$$  __$$\ 
$$\   $$ |$$ /  $$ |$$ |  $$ | \____$$\ $$$$$$$$ | $$$$$$$ |$$ |  \__|$$ /      $$ |  $$ |
$$ |  $$ |$$ |  $$ |$$ |  $$ |$$\   $$ |$$   ____|$$  __$$ |$$ |      $$ |      $$ |  $$ |
\$$$$$$  |\$$$$$$  |$$$$$$$  |\$$$$$$  |\$$$$$$$\ \$$$$$$$ |$$ |      \$$$$$$$\ $$ |  $$ |
 \______/  \______/ \_______/  \______/  \_______| \_______|\__|       \_______|\__|  \__|
                                                                                          
                                                                                          
                                                                                          
"""


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def hyperlink(url: str, text: str = None) -> str:
    """Create a clickable terminal hyperlink using OSC 8 escape codes."""
    if text is None:
        text = url
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 50}{Colors.RESET}\n")


def print_section(title: str):
    print(f"{Colors.BOLD}{Colors.YELLOW}{title}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 40}{Colors.RESET}")


def print_field(label: str, value: str, indent: int = 2):
    spaces = " " * indent
    if value:
        print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET} {value}")
    else:
        print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET} {Colors.DIM}(not set){Colors.RESET}")


def print_list(label: str, items: list, indent: int = 2):
    spaces = " " * indent
    print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET}")
    if items:
        for item in items:
            print(f"{spaces}  {Colors.GREEN}•{Colors.RESET} {item}")
    else:
        print(f"{spaces}  {Colors.DIM}(none){Colors.RESET}")


def display_job_card(job: Job, index: int = None):
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
    
    
def display_job_detail(job: Job):
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
