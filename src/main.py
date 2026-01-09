"""Main CLI for JobSearch application."""
import argparse
from pathlib import Path

from data_handlers import User
from cli_menus import UserOptions

DATA_DIR = Path.home() / ".JobSearch"
if not DATA_DIR.exists():
    DATA_DIR.mkdir()
    
DEFAULT_USER_ID = Path.home().name


def get_or_create_user(user_id: str):
    user_data_dir = DATA_DIR / user_id
    if not user_data_dir.exists():
        is_new_user = True
        user_data_dir.mkdir()
    else:
        if user_data_dir.is_file():
            raise ValueError("directory is a file!")
        is_new_user = False
        
    return User(directory_path=user_data_dir), is_new_user


def main(user_id: str):
    user, is_new_user = get_or_create_user(user_id)
    menu = UserOptions(user)
    if is_new_user:
        menu.first_time_setup()
    menu.main_menu()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobSearch CLI application")
    parser.add_argument("--user_id", "-u", default=DEFAULT_USER_ID, help="User ID for the session")
    args = parser.parse_args()
    main(user_id=args.user_id)