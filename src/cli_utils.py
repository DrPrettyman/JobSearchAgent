"""CLI formatting utilities."""
import os

from data_handlers import Job, JobStatus

DEFAULT_WIDTH = 120


ASCII_ART_JOBSEARCH = r"""   $$$$$\           $$\        $$$$$$\                                          $$\
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
    
    
def pad_middle(text1: str, text2: str, width: int = 30):
    return text1 + text2.rjust(width-len(text1))
    
    
def text_to_lines(text: str, width: int = DEFAULT_WIDTH) -> list[str]:
    words = text.split()
    
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) > width:
            lines.append(line.rstrip())
            line = ""
        line += word + " "
        
    if strip_line := line.strip():
        lines.append(strip_line)
        
    return lines


def print_thick_line(color=Colors.CYAN, width: int = DEFAULT_WIDTH):
    print(f"{Colors.BOLD}{color}{'═' * width}{Colors.RESET}")


def print_header(text: str):
    print()
    print_thick_line()
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.RESET}")
    print_thick_line()
    print()


def print_section(title: str, width: int = DEFAULT_WIDTH):
    print(f"{Colors.BOLD}{Colors.YELLOW}{title}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * width}{Colors.RESET}")


def print_field(label: str, value: str, indent: int = 2, width: int = DEFAULT_WIDTH - 4):
    spaces = " " * indent
    if not value:
        print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET} {Colors.DIM}(not set){Colors.RESET}")
        return
    
    new_line_indent = len(label) + 2
    
    lines = text_to_lines(
        text=value,
        width=width-new_line_indent
    )
    
    print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET} {lines[0]}")
    
    if len(lines) == 1:
        return
    
    padding = " " * (indent + new_line_indent)
    for line in lines[1:]:
        print(padding + line)
    

def print_list(label: str, items: list, indent: int = 2):
    spaces = " " * indent
    print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET}")
    if items:
        for item in items:
            print(f"{spaces}  {Colors.GREEN}•{Colors.RESET} {item}")
    else:
        print(f"{spaces}  {Colors.DIM}(none){Colors.RESET}")
        

def print_numbered_list(label: str, items: list, indent: int = 2, width: int = DEFAULT_WIDTH - 4):
    """Print a numbered list with word wrapping for long items."""
    spaces = " " * indent
    print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET}")
    if items:
        pad = len(str(len(items))) + 1
        item_width = width - indent - 2 - pad  # Account for indent, spacing, and number
        for n, item in enumerate(items, 1):
            n_str = (str(n) + ".").ljust(pad)
            lines = text_to_lines(str(item), width=item_width)
            print(f"{spaces}  {Colors.GREEN}{n_str}{Colors.RESET} {lines[0]}")
            # Continuation lines aligned with first line of text
            continuation_indent = " " * (indent + 2 + pad + 1)
            for line in lines[1:]:
                print(f"{continuation_indent}{line}")
    else:
        print(f"{spaces}  {Colors.DIM}(none){Colors.RESET}")


def print_inline_list(label: str, items: list, indent: int = 2, width: int = DEFAULT_WIDTH - 4, quote: bool = True):
    """Print a comma-separated list with word wrapping.

    Args:
        label: The label to display before the list
        items: List of items to display
        indent: Number of spaces to indent
        width: Maximum width for wrapping
        quote: Whether to wrap items in single quotes
    """
    spaces = " " * indent
    if not items:
        print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET} {Colors.DIM}(none){Colors.RESET}")
        return

    # Format items
    if quote:
        formatted = [f"'{item}'" for item in items]
    else:
        formatted = [str(item) for item in items]

    # Calculate available width for items (after label)
    label_width = len(label) + 2  # ": "
    available_width = width - label_width

    # Build lines with word wrapping
    lines = []
    current_line = ""
    for i, item in enumerate(formatted):
        separator = ", " if i < len(formatted) - 1 else ""
        addition = item + separator

        if not current_line:
            current_line = addition
        elif len(current_line) + len(addition) <= available_width:
            current_line += addition
        else:
            lines.append(current_line.rstrip())
            current_line = addition

    if current_line:
        lines.append(current_line.rstrip())

    # Print first line with label
    print(f"{spaces}{Colors.DIM}{label}:{Colors.RESET} {lines[0]}")

    # Print continuation lines with proper indentation
    continuation_indent = " " * (indent + label_width)
    for line in lines[1:]:
        print(f"{continuation_indent}{line}")


def print_status_summary(applied: int, in_progress: int, pending: int, discarded: int, indent: int = 2):
    """Print a formatted job status summary line."""
    spaces = " " * indent
    parts = []
    if applied:
        parts.append(f"{Colors.GREEN}✓ {applied} applied{Colors.RESET}")
    if in_progress:
        parts.append(f"{Colors.CYAN}▶ {in_progress} in progress{Colors.RESET}")
    if pending:
        parts.append(f"{Colors.YELLOW}○ {pending} pending{Colors.RESET}")
    if discarded:
        parts.append(f"{Colors.RED}✗ {discarded} discarded{Colors.RESET}")

    if parts:
        print(f"{spaces}" + "  •  ".join(parts))


def print_box(title: str, content: str, width: int = DEFAULT_WIDTH - 2, indent: int = 2):
    """Display content inside a bordered box with a title."""
    spaces = " " * indent
    inner_width = width - 4  # Account for border and padding

    # Word wrap the content
    lines = []
    for paragraph in content.split('\n'):
        if not paragraph.strip():
            lines.append('')
            continue
        words = paragraph.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > inner_width:
                lines.append(line.rstrip())
                line = ""
            line += word + " "
        if line.strip():
            lines.append(line.rstrip())

    # Print box
    print(f"{spaces}{Colors.CYAN}╭─ {title} {'─' * (width - len(title) - 5)}╮{Colors.RESET}")
    for line in lines:
        padding = inner_width - len(line)
        print(f"{spaces}{Colors.CYAN}│{Colors.RESET} {line}{' ' * padding} {Colors.CYAN}│{Colors.RESET}")
    print(f"{spaces}{Colors.CYAN}╰{'─' * (width - 2)}╯{Colors.RESET}")


def display_job_card(job: Job, index: int = None):
    """Display a single job as a beautiful card."""
    # Index prefix if provided
    if index is not None:
        prefix = f"{Colors.DIM}[{index}]{Colors.RESET}" + " " * (4 - len(str(index)))
    else:
        prefix = f"{Colors.DIM}[???]{Colors.RESET}"
        
    location = job.location or "Location not specified"
    date = job.date_found[:10] if job.date_found else "Unknown date"
    padding = " " * 6
    
    print(f"{prefix}{Colors.BOLD}{job.company}{Colors.RESET} {Colors.BLUE}📍 {location}{Colors.RESET}")
    print(padding + f"{Colors.CYAN}{job.title}{Colors.RESET} {Colors.BLUE}📅 {date}{Colors.RESET}")

    # # Clickable apply link
    # if job.link:
    #     print(padding + f"{Colors.BLUE}{hyperlink(job.link)}{Colors.RESET}")

    print()
    
    
def display_job_detail(job: Job):
    """Display detailed view of a single job."""
    print_header(f"{job.title} at {job.company}")

    # Status badge
    if job.status == JobStatus.APPLIED:
        print(f"  {Colors.GREEN}━━━ ✓ APPLIED ━━━{Colors.RESET}\n")
    elif job.status == JobStatus.IN_PROGRESS:
        print(f"  {Colors.CYAN}━━━ ▶ IN PROGRESS ━━━{Colors.RESET}\n")
    elif job.status == JobStatus.DISCARDED:
        print(f"  {Colors.RED}━━━ ✗ DISCARDED ━━━{Colors.RESET}\n")
    else:
        print(f"  {Colors.YELLOW}━━━ ○ PENDING ━━━{Colors.RESET}\n")

    # Main info
    print_section("Position Details")
    print_field("Company", job.company)
    print_field("Title", job.title)
    print_field("Location", job.location)
    print_field("Found", job.date_found[:10] if job.date_found else "")
    if job.addressee:
        print_field("Hiring Manager", job.addressee)
    if job.link:
        print_field("Link", job.link)
    print()

    # Description
    if job.description:
        print_section("Summary")
        # Word wrap the description
        lines = text_to_lines(text=job.description, width=DEFAULT_WIDTH - 4)
        for line in lines:
            print("  " + line)
        print()

    # Full description (truncated preview)
    if job.full_description:
        print_section("Full Description")
        if len(job.full_description) > 500:
            preview = job.full_description[:500] + "..."
        else:
            preview = job.full_description
            
        lines = text_to_lines(text=preview, width=DEFAULT_WIDTH - 4)
        for line in lines:
            print("  " + line)
        print(f"\n  {Colors.DIM}({len(job.full_description.split())} words total){Colors.RESET}")
        print()

    # Questions summary
    if job.questions:
        answered = sum(1 for q in job.questions if q.get("answer"))
        total = len(job.questions)
        print_section("Application Questions")
        if answered == total:
            print(f"  {Colors.GREEN}✓ {total} questions answered{Colors.RESET}")
        else:
            print(f"  {Colors.YELLOW}○ {answered}/{total} questions answered{Colors.RESET}")
        print()
