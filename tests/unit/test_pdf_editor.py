from collections.abc import Callable
from pathlib import Path

import pypdf
import pytest

from lf_system.pdf_operationsfolder.exceptions import (
    PDFNotOpenError,
    PDFValidationError,
    PDFWriteError,
)
from lf_system.pdf_operationsfolder.pdf_editor import PDFAdvancedEditor


def test_open_close_and_count_pages(make_pdf: Callable[[str, int], Path], tmp_path: Path) -> None:
    pdf_path = make_pdf("three-pages.pdf", 3)
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)

    assert editor.current_pdf_path == pdf_path
    assert editor.page_count == 3
    assert editor.reader is not None
    assert editor.writer is not None

    editor.close_pdf()

    assert editor.current_pdf_path is None
    assert editor.reader is None
    assert editor.writer is None
    assert editor.page_count == 0
    assert editor.is_modified is False


def test_save_as_writes_copy(make_pdf: Callable[[str, int], Path], tmp_path: Path) -> None:
    pdf_path = make_pdf("original.pdf", 2)
    output_path = tmp_path / "copy.pdf"
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)
    editor.save_as(output_path)

    assert output_path.exists()
    assert len(pypdf.PdfReader(output_path).pages) == 2
    assert editor.current_pdf_path == pdf_path


def test_rotate_pages_and_save(make_pdf: Callable[[str, int], Path], tmp_path: Path) -> None:
    pdf_path = make_pdf("rotate.pdf", 2)
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)
    editor.rotate_pages([1], degrees=90)

    assert editor.is_modified is True
    assert editor.has_unsaved_changes is True

    editor.save()
    saved_reader = pypdf.PdfReader(pdf_path)

    assert saved_reader.pages[0].get("/Rotate") == 90
    assert saved_reader.pages[1].get("/Rotate", 0) == 0
    assert editor.is_modified is False
    assert editor.has_unsaved_changes is False


def test_extract_pages_returns_writer(make_pdf: Callable[[str, int], Path], tmp_path: Path) -> None:
    pdf_path = make_pdf("source.pdf", 4)
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)
    extracted = editor.extract_pages(pages=[1, 3])

    assert len(extracted.pages) == 2


def test_extract_pages_rejects_empty_selection(
    make_pdf: Callable[[str, int], Path], tmp_path: Path
) -> None:
    pdf_path = make_pdf("source.pdf", 4)
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)

    with pytest.raises(PDFValidationError, match="At least one page"):
        editor.extract_pages(pages=[])


@pytest.mark.parametrize("pages", [[0], [-1], [3]])
def test_extract_pages_rejects_out_of_range_page(
    pages: list[int],
    make_pdf: Callable[[str, int], Path], tmp_path: Path
) -> None:
    pdf_path = make_pdf("source.pdf", 2)
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)

    with pytest.raises(PDFValidationError, match="out of range"):
        editor.extract_pages(pages=pages)


def test_extract_pages_rejects_repeated_pages(
    make_pdf: Callable[[str, int], Path], tmp_path: Path
) -> None:
    pdf_path = make_pdf("source.pdf", 2)
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)

    with pytest.raises(PDFValidationError, match="repeated"):
        editor.extract_pages(pages=[1, 1])


def test_export_pages_writes_new_pdf(make_pdf: Callable[[str, int], Path], tmp_path: Path) -> None:
    pdf_path = make_pdf("source.pdf", 4)
    output_path = tmp_path / "pages.pdf"
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)
    result = editor.export_pages(pages_range=(1, 3), output_path=output_path)

    assert result == output_path
    assert len(pypdf.PdfReader(output_path).pages) == 2


def test_watermark_rejects_out_of_range_page(
    make_pdf: Callable[[str, int], Path],
    make_watermark_pdf: Callable[[str], Path],
    tmp_path: Path,
) -> None:
    pdf_path = make_pdf("source.pdf", 1)
    watermark_path = make_watermark_pdf("watermark.pdf")
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)

    with pytest.raises(PDFValidationError, match="out of range"):
        editor.watermark_and_overlay(
            pages=[2],
            output_path=tmp_path / "watermarked.pdf",
            watermark_path=watermark_path,
        )


def test_encrypt_pdf_writes_encrypted_copy(
    make_pdf: Callable[[str, int], Path], tmp_path: Path
) -> None:
    pdf_path = make_pdf("plain.pdf", 2)
    output_path = tmp_path / "encrypted.pdf"
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)

    assert editor.encrypt_pdf("secret", output_path=output_path) is True
    assert editor.has_unsaved_changes is True

    encrypted_reader = pypdf.PdfReader(output_path)
    assert encrypted_reader.is_encrypted is True


def test_decrypt_pdf_writes_plain_copy(
    make_pdf: Callable[[str, int], Path], tmp_path: Path
) -> None:
    pdf_path = make_pdf("plain.pdf", 2)
    encrypted_path = tmp_path / "encrypted.pdf"
    decrypted_path = tmp_path / "decrypted.pdf"
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)
    assert editor.encrypt_pdf("secret", output_path=encrypted_path) is True

    encrypted_editor = PDFAdvancedEditor(tmp_path)
    encrypted_editor.open_pdf(encrypted_path)
    assert encrypted_editor.decrypt_pdf("secret", output_path=decrypted_path) is True
    assert encrypted_editor.has_unsaved_changes is True

    decrypted_reader = pypdf.PdfReader(decrypted_path)
    assert decrypted_reader.is_encrypted is False
    assert len(decrypted_reader.pages) == 2


def test_decrypt_pdf_rejects_wrong_password(
    make_pdf: Callable[[str, int], Path], tmp_path: Path
) -> None:
    pdf_path = make_pdf("plain.pdf", 1)
    encrypted_path = tmp_path / "encrypted.pdf"
    output_path = tmp_path / "should-not-exist.pdf"
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)
    assert editor.encrypt_pdf("secret", output_path=encrypted_path) is True

    encrypted_editor = PDFAdvancedEditor(tmp_path)
    encrypted_editor.open_pdf(encrypted_path)

    assert encrypted_editor.decrypt_pdf("wrong", output_path=output_path) is False
    assert not output_path.exists()


def test_watermark_and_overlay_writes_output(
    make_pdf: Callable[[str, int], Path],
    make_watermark_pdf: Callable[[str], Path],
    tmp_path: Path,
) -> None:
    pdf_path = make_pdf("source.pdf", 2)
    watermark_path = make_watermark_pdf("watermark.pdf")
    output_path = tmp_path / "watermarked.pdf"
    editor = PDFAdvancedEditor(tmp_path)

    editor.open_pdf(pdf_path)
    result = editor.watermark_and_overlay(
        pages=[1],
        output_path=output_path,
        watermark_path=watermark_path,
        over=True,
    )

    assert result is True
    assert editor.has_unsaved_changes is True
    assert output_path.exists()
    assert len(pypdf.PdfReader(output_path).pages) == 2


def test_atomic_write_preserves_original_when_write_fails(
    make_pdf: Callable[[str, int], Path], tmp_path: Path
) -> None:
    class BrokenWriter:
        def write(self, stream) -> None:
            stream.write(b"partial")
            raise OSError("disk full")

    pdf_path = make_pdf("original.pdf", 2)
    editor = PDFAdvancedEditor(tmp_path)
    editor.open_pdf(pdf_path)
    editor.writer = BrokenWriter()

    with pytest.raises(PDFWriteError):
        editor.save()

    assert len(pypdf.PdfReader(pdf_path).pages) == 2


def test_operations_require_open_pdf(tmp_path: Path) -> None:
    editor = PDFAdvancedEditor(tmp_path)

    with pytest.raises(PDFNotOpenError, match="No PDF is open"):
        editor.save()
