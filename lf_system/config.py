"""Central configuration for the LF System.

Holds filesystem paths, default folder layout and constants shared
across the rest of the ``lf_system`` package.
"""

from __future__ import annotations

from pathlib import Path

# Third-party packages required at runtime. Checked dynamically by Main.py
# before importing anything that depends on them.
REQUIRED_PACKAGES: list[str] = [
    "pyperclip",
    "pymsgbox",
    "send2trash",
    "openpyxl",
    "ezsheets",
    "pypdf",
    "pdfminer",
]

# Base folder layout. Everything lives under the user's home directory,
# inside a single "SISTEMA_LF" root, exactly as in the original system.
HOME_DIR: Path = Path.home()
SYSTEM_FOLDER: Path = HOME_DIR / "SISTEMA_LF"
BACKUPS_FOLDER: Path = SYSTEM_FOLDER / "Backups"
SPREADSHEETS_FOLDER: Path = SYSTEM_FOLDER / "Spreadsheets"
DATA_FOLDER: Path = SYSTEM_FOLDER / "Data"
LOGS_FOLDER: Path = SYSTEM_FOLDER / "Logs"
PDFS_PATH: Path = SYSTEM_FOLDER / "PDFs"
# Billing database file names.
BILLING_DB_FILENAME: str = "billing_accounts.sqlite3"

# Misc constants used by the TUI.
ITEMS_PER_PAGE: int = 10
TUI_DIVIDER_WIDTH: int = 85


def ensure_system_directories() -> None:
    """Create every required system folder if it does not exist yet."""
    for folder in (BACKUPS_FOLDER, SPREADSHEETS_FOLDER, DATA_FOLDER, LOGS_FOLDER):
        folder.mkdir(parents=True, exist_ok=True)


def billing_database_path(data_folder: Path) -> Path:
    """Return the SQLite database path for a given data folder."""
    return Path(data_folder) / BILLING_DB_FILENAME
