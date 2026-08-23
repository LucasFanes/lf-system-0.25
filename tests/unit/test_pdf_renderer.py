from collections.abc import Callable
from pathlib import Path

from lf_system.pdf_operationsfolder.pdf_renderer import PDFPageRenderer


def test_renderer_renders_pdf_page_to_png(
    make_pdf: Callable[[str, int], Path], tmp_path: Path
) -> None:
    pdf_path = make_pdf("render.pdf", 1)
    renderer = PDFPageRenderer()

    rendered = renderer.render_page(pdf_path, page_number=1, zoom=1.0)

    assert rendered.image_data.startswith(b"\x89PNG")
    assert rendered.width > 0
    assert rendered.height > 0
