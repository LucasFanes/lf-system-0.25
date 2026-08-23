"""Small shared helpers used across the LF System: PDFReader package."""

from __future__ import annotations

from datetime import datetime


def generate_timestamp() -> str:
    """Return a filesystem-safe timestamp string, e.g. '20260714_185204'."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
