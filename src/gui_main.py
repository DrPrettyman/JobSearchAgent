#!/usr/bin/env python3
"""GUI entry point for JobSearch application."""

import argparse
import getpass

from gui import run_gui


def main():
    parser = argparse.ArgumentParser(description="JobSearch GUI")
    parser.add_argument(
        "-u", "--username",
        default=getpass.getuser(),
        help="Username for the job search profile (default: system username)"
    )
    args = parser.parse_args()

    run_gui(username=args.username)


if __name__ == "__main__":
    main()
