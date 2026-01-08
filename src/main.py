"""Main CLI for JobSearch application."""
from pathlib import Path

from data_handlers import User
from cli_utils import Colors, print_header
from cli_menus import main_menu, user_info_menu

DATA_DIR = Path.home() / ".JobSearch"
if not DATA_DIR.exists():
    IS_NEW_USER = True
    DATA_DIR.mkdir()
else:
    IS_NEW_USER = False


USER = User(directory_path=DATA_DIR)

def main():
    if IS_NEW_USER:
        print_header("Welcome to JobSearch!")
        print(f"{Colors.DIM}Let's set up your profile to get started.{Colors.RESET}\n")
        user_info_menu(USER, skip_first_display=True)
    main_menu(USER)


if __name__ == "__main__":
    main()