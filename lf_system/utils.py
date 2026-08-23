"""Generic helper functions used across the LF System.

Timestamps, terminal screen clearing, simple terminal menus and
graphical (pymsgbox) path prompts live here because they are small,
stateless utilities consumed by several modules.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pymsgbox


def clear_screen() -> None:
    """Clear the terminal screen on both Windows and POSIX systems."""
    os.system("cls" if os.name == "nt" else "clear")


def generate_timestamp() -> str:
    """Return the current timestamp formatted for file names and records."""
    return datetime.now().strftime("%m-%d-%y_%H-%M-%S")


def show_menu(title: str, options: dict[str, str]) -> str | None:
    """Render a simple terminal menu and return the chosen key, or None."""
    print(f"\n==== {title.upper()} ====")
    for key, description in options.items():
        print(f" [{key}] {description}")
    print(" [S] Exit / Cancel")
    print("======================")

    while True:
        choice = input("Choose an option and press Enter: ").strip().lower()
        if choice == "s":
            return None
        if choice in [key.lower() for key in options.keys()]:
            return choice.upper() if choice.isalpha() else choice
        print("Invalid option. Please try again.")


def request_path(message: str) -> Path | None:
    """Prompt (via pymsgbox) for a filesystem path until a valid one is given."""
    while True:
        user_input = pymsgbox.prompt(
            text=f"{message}\nor type 'S' to exit",
            title="Path Input",
        )
        if user_input is None or user_input.strip().lower() == "s":
            return None

        path = Path(user_input.strip().replace('"', ""))
        if path.exists():
            return path

        pymsgbox.alert("Invalid path or path not found.", "Error")
