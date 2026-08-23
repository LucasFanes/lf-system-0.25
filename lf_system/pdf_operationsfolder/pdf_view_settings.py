"""Pure view calculations for the PDF graphical editor."""

from __future__ import annotations

from typing import Literal

ZoomMode = Literal["fit_window", "fit_width", "actual_size", "manual"]


def calculate_zoom(
    mode: ZoomMode,
    page_width: float,
    page_height: float,
    viewport_width: int,
    viewport_height: int,
    manual_zoom: float,
) -> float:
    """Return a proportional render zoom for the current viewer mode."""
    if mode == "actual_size":
        return 1.0
    if mode == "manual":
        return _clamp_zoom(manual_zoom)

    usable_width = max(1, viewport_width - 32)
    usable_height = max(1, viewport_height - 32)
    width_zoom = usable_width / max(1.0, page_width)

    if mode == "fit_width":
        return _clamp_zoom(width_zoom)

    height_zoom = usable_height / max(1.0, page_height)
    return _clamp_zoom(min(width_zoom, height_zoom))


def _clamp_zoom(zoom: float) -> float:
    return round(min(3.0, max(0.25, zoom)), 2)
