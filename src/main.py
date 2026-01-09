"""Main CLI for JobSearch application."""
import argparse
from pathlib import Path

from data_handlers import User
from cli_menus import UserOptions

DATA_DIR = Path.home() / ".JobSearch"
if not DATA_DIR.exists():
    DATA_DIR.mkdir()
    
DEFAULT_USER_ID = Path.home().name


def main(user_id: str):
    user = User(directory_path=DATA_DIR / user_id)
    menu = UserOptions(user)
    menu.main_menu()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobSearch CLI application")
    parser.add_argument("--user_id", "-u", default=DEFAULT_USER_ID, help="User ID for the session")
    args = parser.parse_args()
    main(user_id=args.user_id)