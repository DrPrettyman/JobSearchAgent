"""Main CLI for JobSearch application."""
import argparse
from pathlib import Path

from data_handlers import User
from cli_menus import UserOptions

DEFAULT_USERNAME = Path.home().name


def main(username: str):
    user = User(username=username)
    menu = UserOptions(user)
    menu.main_menu()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobSearch CLI application")
    parser.add_argument("--username", "-u", default=DEFAULT_USERNAME, help="Username for the session")
    args = parser.parse_args()
    main(username=args.username)