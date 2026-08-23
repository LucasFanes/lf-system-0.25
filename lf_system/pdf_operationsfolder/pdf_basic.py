import logging
from pathlib import Path

import pypdf  # type: ignore

from .exceptions import PDFNotOpenError

logger = logging.getLogger(__name__)


class BasicPDFOperations:
    """Basic operations for PDF files."""

    def __init__(self, pdfs_path: Path, writeback: bool = False) -> None:
        self.pdfs_path = pdfs_path
        self.writeback = writeback

        self.current_pdf_path: Path | None = None
        self.reader: pypdf.PdfReader | None = None
        self.writer: pypdf.PdfWriter | None = None
        self.is_modified: bool = False
        self.page_count: int = 0

    # ------------------------------------------------------------------
    # Persistence — the ONLY methods allowed to write PDF bytes to disk
    # ------------------------------------------------------------------
    @staticmethod
    def _write(writer: pypdf.PdfWriter, output_path: str | Path) -> None:
        with open(output_path, "wb") as file:
            writer.write(file)

    def save(self) -> None:
        """Write the in-memory changes back to the currently open file."""
        self._ensure_open()
        if self.current_pdf_path is None:
            raise RuntimeError("No file path associated with the open PDF.")

        self._write(self.writer, self.current_pdf_path)
        self.is_modified = False
        logger.info("Saved changes to %s.", self.current_pdf_path)

    def save_as(self, output_path: str | Path) -> None:
        """Write the in-memory changes to a new file, keeping the original."""
        self._ensure_open()
        self._write(self.writer, output_path)
        logger.info("Saved a copy to %s.", output_path)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open_pdf(self, pdf_path: str | Path) -> None:
        """Open a PDF and load it into memory.

        The reader is used for read-only operations; the writer holds a
        working copy of every page so in-place edits (like rotation) have
        somewhere to accumulate before :meth:`save`/:meth:`save_as`.
        """
        pdf_path = Path(pdf_path)

        reader = pypdf.PdfReader(pdf_path)
        writer = pypdf.PdfWriter()
        page_count = 0

        if not reader.is_encrypted:
            writer.append(reader)
            page_count = len(reader.pages)

        self.current_pdf_path = pdf_path
        self.reader = reader
        self.writer = writer
        self.page_count = page_count
        self.is_modified = False

        logger.info("Opened PDF: %s (%d pages).", pdf_path, self.page_count)

    def close_pdf(self) -> None:
        """Discard the in-memory PDF. Unsaved changes are lost."""
        self.current_pdf_path = None
        self.reader = None
        self.writer = None
        self.page_count = 0
        self.is_modified = False

        logger.info("PDF closed.")

    def _ensure_open(self) -> None:
        if self.reader is None or self.writer is None:
            raise PDFNotOpenError("No PDF is open. Call open_pdf() first.")

    def _ensure_open_with_path(self) -> None:
        self._ensure_open()
        if self.current_pdf_path is None:
            raise RuntimeError("No file path is associated with the currently open PDF.")
