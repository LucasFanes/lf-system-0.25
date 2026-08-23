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

import pypdf  # type: ignore

from .pdf_basic import BasicPDFOperations

logger = logging.getLogger(__name__)


class PDFEditor2(BasicPDFOperations):
    """Extends :class:`PDFEditor` with password protection operations.

    Builds on top of :class:`PDFEditor` (rotation, text extraction, image
    extraction, page export, watermarking) so a single instance exposes the
    full set of operations. Only :meth:`save`/:meth:`save_as` (inherited)
    and the methods below write PDF bytes to disk.
    """
    
    def __init__(self, pdfs_path, writeback=False):
        super().__init__(pdfs_path, writeback)
        
    def encrypt_pdf(self, password: str, output_path: str | Path | None = None) -> bool:
        """Encrypt the currently open PDF with a password.

        If ``output_path`` is provided, the encrypted PDF will be saved to
        that path. If not, it will overwrite the currently open PDF.
        """
        self._ensure_open_with_path()
        output_path = Path(output_path) if output_path else self.current_pdf_path

        try:
            self.writer.encrypt(password, algorithm="AES-256")
            self._write(self.writer, output_path)
            logger.info("Encrypted PDF saved to %s.", output_path)
            return True
        except Exception:
            logger.exception("Failed to encrypt PDF.")
            return False

    def decrypt_pdf(self, password: str, output_path: str | Path | None = None) -> bool:
        """Decrypt the currently open PDF with a password.

        If ``output_path`` is provided, the decrypted PDF will be saved to
        that path. If not, it will overwrite the currently open PDF.
        """
        self._ensure_open_with_path()
        output_path = Path(output_path) if output_path else self.current_pdf_path

        if not self.reader.is_encrypted:
            logger.warning("The PDF is not encrypted. No decryption needed.")
            return False

        try:
            result = self.reader.decrypt(password)

            if result.name == "NOT_DECRYPTED":
                raise ValueError("Incorrect password.")

            # Now that the reader is decrypted, its pages can be copied.
            # Refresh self.writer/page_count too, so subsequent operations
            # (rotate_pages, save, ...) work against the decrypted content.
            self.writer = pypdf.PdfWriter()
            self.writer.append(self.reader)
            self.page_count = len(self.reader.pages)

            self._write(self.writer, output_path)
            logger.info("Decrypted PDF saved to %s.", output_path)
            return True
        except Exception:
            logger.exception("Failed to decrypt PDF.")
            return False
