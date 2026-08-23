"""Entry point for the LF System TUI.

Kept at the project root so the system is still launched with
``python Main.py``. All real logic lives in the ``lf_system`` package.
"""

from __future__ import annotations

import importlib
import sys

from lf_system.config import REQUIRED_PACKAGES
from lf_system.logging_config import setup_logging


def ensure_required_packages() -> None:
    """Validate runtime dependencies before opening the TUI."""
    for package_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package_name)
        except ModuleNotFoundError:
            print(f"\n[CRITICAL ERROR] Required library missing: '{package_name}'.")
            print(f"Please run this command in your terminal: pip install {package_name}")
            input("\nPress Enter to close the system...")
            sys.exit()


def main() -> None:
    ensure_required_packages()
    setup_logging()

    from lf_system.app import LFSystem

    system = LFSystem()
    system.modern_loading_screen()
    system.interface_loop()


if __name__ == "__main__":
    main()
