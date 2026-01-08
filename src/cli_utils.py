"""CLI formatting utilities."""


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
