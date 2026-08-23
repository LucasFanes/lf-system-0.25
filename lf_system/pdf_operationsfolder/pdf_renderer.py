"""PDF page rendering helpers for the graphical editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(frozen=True)
class RenderedPage:
    image_data: bytes
    width: int
    height: int


class PDFPageRenderer:
    """Render PDF pages to PNG bytes using PyMuPDF."""

    def page_size(self, pdf_source: bytes | str | Path, page_number: int) -> tuple[float, float]:
        document = self._open_document(pdf_source)
        try:
            page = document.load_page(page_number - 1)
            rect = page.rect
            return rect.width, rect.height
        finally:
            document.close()

    def render_page(
        self,
        pdf_source: bytes | str | Path,
        page_number: int,
        zoom: float,
    ) -> RenderedPage:
        document = self._open_document(pdf_source)
        try:
            page = document.load_page(page_number - 1)
            matrix = pymupdf.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            return RenderedPage(
                image_data=pixmap.tobytes("png"),
                width=pixmap.width,
                height=pixmap.height,
            )
        finally:
            document.close()

    def _open_document(self, pdf_source: bytes | str | Path) -> pymupdf.Document:
        if isinstance(pdf_source, bytes):
            return pymupdf.open(stream=pdf_source, filetype="pdf")
        return pymupdf.open(str(pdf_source))
