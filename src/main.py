"""Main entry point for JobSearch application."""
import argparse
from pathlib import Path

DEFAULT_USERNAME = Path.home().name


def main_cli(username: str):
    """Run the CLI interface."""
    from data_handlers import User
    from cli_menus import UserOptions

    user = User(username=username)
    menu = UserOptions(user)
    menu.main_menu()


def main_gui(username: str):
    """Run the GUI interface."""
    from gui import run_gui
    run_gui(username=username)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobSearch application")
    parser.add_argument("--username", "-u", default=DEFAULT_USERNAME, help="Username for the session")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch GUI instead of CLI")
    args = parser.parse_args()

    if args.gui:
        main_gui(username=args.username)
    else:
        main_cli(username=args.username)