from lf_system.pdf_operationsfolder.pdf_view_settings import calculate_zoom


def test_fit_window_zoom_preserves_page_proportion() -> None:
    zoom = calculate_zoom(
        mode="fit_window",
        page_width=600,
        page_height=900,
        viewport_width=1200,
        viewport_height=700,
        manual_zoom=1.0,
    )

    assert zoom == 0.74


def test_fit_width_uses_available_width() -> None:
    zoom = calculate_zoom(
        mode="fit_width",
        page_width=600,
        page_height=900,
        viewport_width=1200,
        viewport_height=700,
        manual_zoom=1.0,
    )

    assert zoom == 1.95


def test_actual_size_ignores_viewport() -> None:
    assert calculate_zoom("actual_size", 600, 900, 100, 100, 2.0) == 1.0


def test_manual_zoom_is_clamped() -> None:
    assert calculate_zoom("manual", 600, 900, 100, 100, 8.0) == 3.0
    assert calculate_zoom("manual", 600, 900, 100, 100, 0.1) == 0.25
