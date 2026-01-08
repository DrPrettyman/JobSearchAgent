"""Main CLI for JobSearch application."""

from data_handlers import USER
from cli_utils import Colors, print_header
from cli_menus import main_menu, user_info_menu


def main():
    if USER.is_new_user:
        print_header("Welcome to JobSearch!")
        print(f"{Colors.DIM}Let's set up your profile to get started.{Colors.RESET}\n")
        user_info_menu(USER, skip_first_display=True)
    main_menu(USER)


if __name__ == "__main__":
    main()
