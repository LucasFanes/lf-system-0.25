"""Domain layer for the LF System: PDFReader.

This module defines :class:`PDFEditor`, a small domain object that keeps a
single PDF open in memory and exposes editing operations over it. It has
no knowledge of any user interface (CLI, TUI, GUI, or API) — those are
expected to be built as thin layers on top of this class, calling its
public methods and handling their own input/output and error display.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import pdfminer.high_level
import pypdf

from .exceptions import PDFPasswordError, PDFValidationError, PDFWriteError
from .pdf_basic import BasicPDFOperations
from .utils import generate_timestamp

logger = logging.getLogger(__name__)

PageRange = tuple[int, int] | tuple[int, int, int]


class PDFEditor(BasicPDFOperations):
    """Keeps a single PDF open in memory and edits it in place.

    All operations (:meth:`rotate_pages`, :meth:`read_text`,
    :meth:`extract_images`, :meth:`extract_pages`, ...) work against the
    PDF already loaded by :meth:`open_pdf` — none of them accept a
    ``pdf_path`` argument or reopen the file. Only :meth:`save` and
    :meth:`save_as` write to disk; every other method only mutates the
    in-memory state and, when relevant, sets ``is_modified``.
    """

    def __init__(self, pdfs_path: str | Path, writeback: bool = False) -> None:
        super().__init__(pdfs_path, writeback)

    # ------------------------------------------------------------------
    # Persistence — the ONLY methods allowed to write PDF bytes to disk
    # ------------------------------------------------------------------
    @staticmethod
    def _write(writer: pypdf.PdfWriter, output_path: str | Path) -> None:
        target_path = Path(output_path)
        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                "wb",
                delete=False,
                dir=target_path.parent,
                prefix=f".{target_path.name}.",
                suffix=".tmp",
            ) as file:
                temp_path = Path(file.name)
                writer.write(file)

            os.replace(temp_path, target_path)
        except Exception as exc:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise PDFWriteError(f"Failed to write PDF file: {target_path}") from exc

    @property
    def has_unsaved_changes(self) -> bool:
        return self.is_modified

    def _resolve_current_output_path(self, output_path: str | Path | None) -> Path:
        if output_path is not None:
            return Path(output_path)
        self._ensure_open_with_path()
        return self.current_pdf_path

    def _selected_page_indices(
        self,
        pages: list[int] | None = None,
        pages_range: PageRange | None = None,
    ) -> list[int]:
        if pages is None and pages_range is None:
            raise PDFValidationError("Either 'pages' or 'pages_range' must be provided.")

        if pages is not None:
            indices = [page_number - 1 for page_number in pages]
        else:
            indices = list(range(*pages_range))

        self._validate_page_indices(indices)
        return indices

    def _validate_page_indices(self, indices: list[int]) -> None:
        if not indices:
            raise PDFValidationError("At least one page must be selected.")

        repeated_pages = sorted(
            {page_index + 1 for page_index in indices if indices.count(page_index) > 1}
        )
        if repeated_pages:
            raise PDFValidationError(f"Selected page(s) repeated: {repeated_pages}.")

        invalid_pages = [
            page_index + 1
            for page_index in indices
            if page_index < 0 or page_index >= self.page_count
        ]
        if invalid_pages:
            raise PDFValidationError(
                f"Selected page(s) out of range: {invalid_pages}. "
                f"Available pages: 1-{self.page_count}."
            )

    def save(self) -> None:
        """Write the in-memory changes back to the currently open file."""
        output_path = self._resolve_current_output_path(None)
        self._write(self.writer, output_path)
        self.is_modified = False
        logger.info("Saved changes to %s.", output_path)

    def save_as(self, output_path: str | Path) -> None:
        """Write the in-memory changes to a new file, keeping the original."""
        self._ensure_open()
        self._write(self.writer, output_path)
        logger.info("Saved a copy to %s.", output_path)

    # ------------------------------------------------------------------
    # Read-only operations
    # ------------------------------------------------------------------
    def read_text(self) -> str:
        """Return the text content of the currently open PDF."""
        self._ensure_open()
        try:
            text = "".join((page.extract_text() or "") + "\n" for page in self.reader.pages)
            logger.info("Read text from %s using pypdf.", self.current_pdf_path)
            return text
        except Exception as exc:
            logger.error("Error reading PDF with pypdf: %s. Trying pdfminer...", exc)
            try:
                return pdfminer.high_level.extract_text(self.current_pdf_path)
            except Exception as exc2:
                logger.error("Error reading PDF with pdfminer: %s.", exc2)
                raise RuntimeError(f"Failed to read PDF file: {self.current_pdf_path}") from exc2

    def extract_images(self, output_folder: str | Path) -> int:
        """Extract every embedded image from the open PDF into a folder.

        Returns the number of images extracted. This writes image files,
        not the PDF itself, so it does not go through save()/save_as().
        """
        self._ensure_open()
        output_folder = Path(output_folder)
        image_count = 0

        try:
            for page_number, page in enumerate(self.reader.pages, start=1):
                logger.info(
                    "Extracting images from page %d of %d...", page_number, self.page_count
                )
                for image in page.images:
                    image_path = (
                        output_folder
                        / f"image_{image_count}_page{page_number}_{image.name}"
                    )
                    with open(image_path, "wb") as file:
                        file.write(image.data)
                    image_count += 1

            logger.info("Extracted %d images from %s.", image_count, self.current_pdf_path)
            return image_count
        except Exception as exc:
            logger.error("Error extracting images from PDF: %s", exc)
            return image_count

    # ------------------------------------------------------------------
    # In-memory editing operations
    # ------------------------------------------------------------------
    def rotate_pages(self, pages: list[int], degrees: int = 90) -> None:
        """Rotate the given 1-indexed pages of the open PDF, in memory.

        Nothing is written to disk here — call :meth:`save` or
        :meth:`save_as` afterward to persist the change.
        """
        self._ensure_open()
        logger.info(
            "Rotating pages %s of %s by %d degrees.", pages, self.current_pdf_path, degrees
        )

        for index, page in enumerate(self.writer.pages, start=1):
            if index in pages:
                page.rotate(degrees)
                logger.info("Rotated page %d by %d degrees.", index, degrees)

        self.is_modified = True

    def extract_pages(
        self,
        pages: list[int] | None = None,
        pages_range: PageRange | None = None,
    ) -> pypdf.PdfWriter:
        """Build a new in-memory PDF from a subset of pages of the open PDF.

        ``pages`` uses 1-indexed page numbers, consistent with the rest of
        this class (e.g. :meth:`rotate_pages`); it is converted to the
        0-indexed list pypdf expects before being passed along. The result
        is returned as a :class:`pypdf.PdfWriter` and is not written to
        disk — use :meth:`export_pages` to also save it.
        """
        self._ensure_open()
        selected = self._selected_page_indices(pages=pages, pages_range=pages_range)

        logger.info(
            "Extracting pages %s or range %s from %s.", pages, pages_range, self.current_pdf_path
        )

        extracted = pypdf.PdfWriter()
        extracted.append(self.reader, pages=selected)
        return extracted

    def export_pages(
        self,
        pages: list[int] | None = None,
        pages_range: PageRange | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Extract pages from the open PDF and save them as a new file.

        This is the one place besides save()/save_as() that writes PDF
        bytes to disk, and it does so through the same internal
        ``_write`` helper, for a brand-new document rather than the
        currently open one.
        """
        extracted = self.extract_pages(pages=pages, pages_range=pages_range)
        output_path = Path(output_path) if output_path else Path(f"PDF{generate_timestamp()}.pdf")

        self._write(extracted, output_path)
        logger.info(
            "New PDF created at %s from pages %s / range %s.", output_path, pages, pages_range
        )
        return output_path

    def watermark_and_overlay(
        self,
        pages: list[int] | None = None,
        pages_range: PageRange | None = None,
        output_path: str | Path | None = None,
        watermark_path: str | Path | None = None,
        over: bool = False,
    ) -> bool:
        """Add a watermark or overlay to selected pages and save the result."""
        logger.info("Adding watermark/overlay.")
        self._ensure_open()

        if output_path is None:
            raise PDFValidationError("'output_path' must be provided.")
        if watermark_path is None:
            raise PDFValidationError("'watermark_path' must be provided.")

        indices = self._selected_page_indices(pages=pages, pages_range=pages_range)

        try:
            watermark_page = pypdf.PdfReader(watermark_path).pages[0]

            for index in indices:
                self.writer.pages[index].merge_page(watermark_page, over=over)

            self._write(self.writer, output_path)
            self.is_modified = Path(output_path) != self.current_pdf_path

            logger.info("Watermark/overlay saved to %s.", output_path)
            return True

        except Exception:
            logger.exception("Failed to add watermark/overlay.")
            return False


class PDFAdvancedEditor(PDFEditor):
    """Extends :class:`PDFEditor` with password protection operations."""

    def encrypt_pdf(self, password: str, output_path: str | Path | None = None) -> bool:
        """Encrypt the currently open PDF with a password."""
        self._ensure_open_with_path()
        resolved_output_path = self._resolve_current_output_path(output_path)

        try:
            self.writer.encrypt(password, algorithm="AES-256")
            self._write(self.writer, resolved_output_path)
            self.is_modified = resolved_output_path != self.current_pdf_path
            logger.info("Encrypted PDF saved to %s.", resolved_output_path)
            return True
        except Exception:
            logger.exception("Failed to encrypt PDF.")
            return False

    def decrypt_pdf(self, password: str, output_path: str | Path | None = None) -> bool:
        """Decrypt the currently open PDF with a password."""
        self._ensure_open_with_path()
        resolved_output_path = self._resolve_current_output_path(output_path)

        if not self.reader.is_encrypted:
            logger.warning("The PDF is not encrypted. No decryption needed.")
            return False

        try:
            result = self.reader.decrypt(password)

            if result.name == "NOT_DECRYPTED":
                raise PDFPasswordError("Incorrect password.")

            self.writer = pypdf.PdfWriter()
            self.writer.append(self.reader)
            self.page_count = len(self.reader.pages)

            self._write(self.writer, resolved_output_path)
            self.is_modified = resolved_output_path != self.current_pdf_path
            logger.info("Decrypted PDF saved to %s.", resolved_output_path)
            return True
        except Exception:
            logger.exception("Failed to decrypt PDF.")
            return False
