from collections.abc import Callable
from pathlib import Path

import pypdf
import pytest


@pytest.fixture
def make_pdf(tmp_path: Path) -> Callable[[str, int], Path]:
    def _make_pdf(name: str = "sample.pdf", pages: int = 3) -> Path:
        path = tmp_path / name
        writer = pypdf.PdfWriter()
        for index in range(pages):
            writer.add_blank_page(width=200 + index, height=300 + index)
        with path.open("wb") as file:
            writer.write(file)
        return path

    return _make_pdf


@pytest.fixture
def make_watermark_pdf(tmp_path: Path) -> Callable[[str], Path]:
    def _make_watermark_pdf(name: str = "watermark.pdf") -> Path:
        path = tmp_path / name
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=200, height=300)
        with path.open("wb") as file:
            writer.write(file)
        return path

    return _make_watermark_pdf
