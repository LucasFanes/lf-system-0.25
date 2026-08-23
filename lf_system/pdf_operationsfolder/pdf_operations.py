"""Domain layer for the LF System: PDFReader.

This module defines :class:`PDFEditor`, a small domain object that keeps a
single PDF open in memory and exposes editing operations over it. It has
no knowledge of any user interface (CLI, TUI, GUI, or API) — those are
expected to be built as thin layers on top of this class, calling its
public methods and handling their own input/output and error display.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pdfminer.high_level  # type: ignore
import pypdf  # type: ignore

from .pdf_basic import BasicPDFOperations
from .utils import generate_timestamp

logger = logging.getLogger(__name__)


class PDFEditor(BasicPDFOperations):
    """Keeps a single PDF open in memory and edits it in place.

    All operations (:meth:`rotate_pages`, :meth:`read_text`,
    :meth:`extract_images`, :meth:`extract_pages`, ...) work against the
    PDF already loaded by :meth:`open_pdf` — none of them accept a
    ``pdf_path`` argument or reopen the file. Only :meth:`save` and
    :meth:`save_as` write to disk; every other method only mutates the
    in-memory state and, when relevant, sets ``is_modified``.
    """

    def __init__(self, pdfs_path, writeback=False):
        super().__init__(pdfs_path, writeback)

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
                    image_name = f"image_{image_count}_page{page_number}_{image.name}"
                    image_path = output_folder / image_name
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
        pages_range: tuple[int, int] | tuple[int, int, int] | None = None,
    ) -> pypdf.PdfWriter:
        """Build a new in-memory PDF from a subset of pages of the open PDF.

        The result is returned as a :class:`pypdf.PdfWriter` and is not
        written to disk — use :meth:`export_pages` to also save it.
        """
        self._ensure_open()
        if pages is None and pages_range is None:
            raise ValueError("Either 'pages' or 'pages_range' must be provided.")

        logger.info(
            "Extracting pages %s or range %s from %s.", pages, pages_range, self.current_pdf_path
        )

        extracted = pypdf.PdfWriter()
        extracted.append(self.reader, pages=pages if pages is not None else pages_range)
        return extracted

    def export_pages(
        self,
        pages: list[int] | None = None,
        pages_range: tuple[int, int] | tuple[int, int, int] | None = None,
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
        pages_range: tuple[int, int] | tuple[int, int, int] | None = None,
        output_path: str | Path | None = None,
        watermark_path: str | Path | None = None,
        over: bool = False,
    ) -> bool:
        """Add a watermark or overlay to selected pages and save the result."""
        logger.info("Adding watermark/overlay.")
        self._ensure_open()

        if pages is None and pages_range is None:
            raise ValueError("Either 'pages' or 'pages_range' must be provided.")
        if output_path is None:
            raise ValueError("'output_path' must be provided.")
        if watermark_path is None:
            raise ValueError("'watermark_path' must be provided.")

        try:
            watermark_page = pypdf.PdfReader(watermark_path).pages[0]
            selected_pages = pages if pages is not None else pages_range

            for page in self.writer.pages(pages=selected_pages):
                page.merge_page(watermark_page, over=over)

            self._write(self.writer, output_path)

            logger.info("Watermark/overlay saved to %s.", output_path)
            return True

        except Exception:
            logger.exception("Failed to add watermark/overlay.")
            return False
