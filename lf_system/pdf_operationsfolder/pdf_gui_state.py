"""State objects for the PDF graphical interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .pdf_view_settings import ZoomMode


@dataclass(frozen=True)
class PDFGuiState:
    current_file: Path | None = None
    page_count: int = 0
    selected_page: int = 0
    zoom: float = 1.0
    zoom_mode: ZoomMode = "fit_window"
    pages_panel_visible: bool = True
    tools_panel_visible: bool = True
    has_unsaved_changes: bool = False
    is_busy: bool = False
    status_message: str = "Nenhum PDF aberto."

    @property
    def has_open_pdf(self) -> bool:
        return self.current_file is not None

    @property
    def file_name(self) -> str:
        return self.current_file.name if self.current_file else "Nenhum arquivo"

    @property
    def can_save(self) -> bool:
        return self.has_open_pdf and self.has_unsaved_changes and not self.is_busy

    @property
    def can_use_pdf_tools(self) -> bool:
        return self.has_open_pdf and not self.is_busy

    @property
    def can_go_previous(self) -> bool:
        return self.can_use_pdf_tools and self.selected_page > 1

    @property
    def can_go_next(self) -> bool:
        return self.can_use_pdf_tools and self.selected_page < self.page_count

    @property
    def can_zoom_out(self) -> bool:
        return self.can_use_pdf_tools and self.zoom_mode == "manual" and self.zoom > 0.25

    @property
    def can_zoom_in(self) -> bool:
        return self.can_use_pdf_tools and self.zoom_mode == "manual" and self.zoom < 3.0

    @property
    def selected_page_label(self) -> str:
        if not self.has_open_pdf:
            return "Página: -"
        return f"Página: {self.selected_page}/{self.page_count}"

    @property
    def change_label(self) -> str:
        return "Alterações pendentes" if self.has_unsaved_changes else "Sem alterações"

    @property
    def zoom_label(self) -> str:
        labels = {
            "fit_window": "Ajustar à janela",
            "fit_width": "Ajustar à largura",
            "actual_size": "Tamanho real",
            "manual": f"Manual {int(self.zoom * 100)}%",
        }
        return f"Zoom: {labels[self.zoom_mode]}"

    def button_states(self) -> dict[str, str]:
        open_state = "disabled" if self.is_busy else "normal"
        tool_state = "normal" if self.can_use_pdf_tools else "disabled"
        save_state = "normal" if self.can_save else "disabled"
        return {
            "open": open_state,
            "close": tool_state,
            "save": save_state,
            "save_as": tool_state,
            "rotate_left": tool_state,
            "rotate_right": tool_state,
            "extract_pages": tool_state,
            "extract_images": tool_state,
            "watermark": tool_state,
            "encrypt": tool_state,
            "decrypt": tool_state,
            "previous_page": "normal" if self.can_go_previous else "disabled",
            "next_page": "normal" if self.can_go_next else "disabled",
            "zoom_out": "normal" if self.can_zoom_out else "disabled",
            "zoom_in": "normal" if self.can_zoom_in else "disabled",
            "fit_window": tool_state,
            "fit_width": tool_state,
            "actual_size": tool_state,
            "manual_zoom": tool_state,
            "toggle_pages": open_state,
            "toggle_tools": open_state,
            "fullscreen": open_state,
        }
