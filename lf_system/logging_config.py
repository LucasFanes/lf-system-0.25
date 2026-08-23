"""Logging configuration for the LF System."""

from __future__ import annotations

import logging

from .config import LOGS_FOLDER

_configured = False


def setup_logging() -> None:
    """Configure the root logger to write to the LF System log file.

    Safe to call multiple times: configuration is only applied once.
    """
    global _configured
    if _configured:
        return

    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOGS_FOLDER / "Logs.txt",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        encoding="utf-8",
    )
    logging.info("================ LF SYSTEM STARTED ================")
    _configured = True
