"""Controller for the standalone PDF graphical interface."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from io import BytesIO
from pathlib import Path

from .exceptions import PDFError, PDFValidationError
from .pdf_editor import PDFAdvancedEditor
from .pdf_gui_state import PDFGuiState
from .pdf_view_settings import ZoomMode

ConfirmationCallback = Callable[[str, str], bool]


class PDFGuiController:
    """Coordinates GUI actions without duplicating PDF domain rules."""

    def __init__(
        self,
        pdfs_path: str | Path,
        editor: PDFAdvancedEditor | None = None,
        confirm: ConfirmationCallback | None = None,
    ) -> None:
        self.editor = editor or PDFAdvancedEditor(pdfs_path)
        self._confirm = confirm or (lambda _title, _message: True)
        self.state = PDFGuiState()

    def open_pdf(self, pdf_path: str | Path) -> PDFGuiState:
        if not self.can_replace_current_pdf():
            return self._set_status("Abertura cancelada.")

        self.editor.open_pdf(pdf_path)
        selected_page = 1 if self.editor.page_count else 0
        self.state = PDFGuiState(
            current_file=self.editor.current_pdf_path,
            page_count=self.editor.page_count,
            selected_page=selected_page,
            has_unsaved_changes=self.editor.has_unsaved_changes,
            status_message="PDF aberto com sucesso.",
        )
        return self.state

    def close_pdf(self) -> PDFGuiState:
        if not self.can_replace_current_pdf():
            return self._set_status("Fechamento cancelado.")

        self.editor.close_pdf()
        self.state = PDFGuiState(status_message="PDF fechado.")
        return self.state

    def can_replace_current_pdf(self) -> bool:
        if not self.state.has_unsaved_changes:
            return True
        return self._confirm(
            "Alterações não salvas",
            "Existem alterações não salvas. Deseja continuar mesmo assim?",
        )

    def save(self) -> PDFGuiState:
        return self._run_operation("PDF salvo.", self.editor.save)

    def save_as(self, output_path: str | Path) -> PDFGuiState:
        return self._run_operation("PDF salvo como novo arquivo.", self.editor.save_as, output_path)

    def rotate_left(self) -> PDFGuiState:
        return self._rotate(-90, "Página girada à esquerda.")

    def rotate_right(self) -> PDFGuiState:
        return self._rotate(90, "Página girada à direita.")

    def extract_pages(self, pages: list[int], output_path: str | Path) -> PDFGuiState:
        return self._run_operation(
            "Páginas extraídas com sucesso.",
            self.editor.export_pages,
            pages=pages,
            output_path=output_path,
        )

    def extract_images(self, output_folder: str | Path) -> PDFGuiState:
        def operation() -> None:
            count = self.editor.extract_images(output_folder)
            self.state = replace(self.state, status_message=f"Imagens extraídas: {count}.")

        return self._run_operation(None, operation)

    def apply_watermark(
        self,
        watermark_path: str | Path,
        output_path: str | Path,
        pages: list[int] | None = None,
    ) -> PDFGuiState:
        target_pages = pages or self._all_pages()
        return self._run_operation(
            "Marca-d'água aplicada com sucesso.",
            self.editor.watermark_and_overlay,
            pages=target_pages,
            output_path=output_path,
            watermark_path=watermark_path,
            over=True,
        )

    def encrypt(self, password: str, output_path: str | Path | None = None) -> PDFGuiState:
        self._require_password(password)
        return self._run_boolean_operation(
            "PDF criptografado com sucesso.",
            "Não foi possível criptografar o PDF.",
            self.editor.encrypt_pdf,
            password,
            output_path=output_path,
        )

    def decrypt(self, password: str, output_path: str | Path | None = None) -> PDFGuiState:
        self._require_password(password)
        return self._run_boolean_operation(
            "PDF descriptografado com sucesso.",
            "Não foi possível descriptografar o PDF.",
            self.editor.decrypt_pdf,
            password,
            output_path=output_path,
        )

    def select_page(self, page_number: int) -> PDFGuiState:
        if not self.state.has_open_pdf:
            return self._set_status("Nenhum PDF aberto.")
        if page_number < 1 or page_number > self.state.page_count:
            raise PDFValidationError("Página selecionada fora dos limites.")
        self.state = replace(self.state, selected_page=page_number)
        return self.state

    def previous_page(self) -> PDFGuiState:
        if self.state.can_go_previous:
            return self.select_page(self.state.selected_page - 1)
        return self._set_status("Você já está na primeira página.")

    def next_page(self) -> PDFGuiState:
        if self.state.can_go_next:
            return self.select_page(self.state.selected_page + 1)
        return self._set_status("Você já está na última página.")

    def zoom_in(self) -> PDFGuiState:
        return self._set_zoom(min(3.0, self.state.zoom + 0.25), mode="manual")

    def zoom_out(self) -> PDFGuiState:
        return self._set_zoom(max(0.25, self.state.zoom - 0.25), mode="manual")

    def set_zoom_mode(self, mode: ZoomMode) -> PDFGuiState:
        if mode == "actual_size":
            return self._set_zoom(1.0, mode=mode)
        return self._set_zoom(self.state.zoom, mode=mode)

    def set_effective_zoom(self, zoom: float) -> PDFGuiState:
        self.state = replace(self.state, zoom=round(zoom, 2))
        return self.state

    def toggle_pages_panel(self) -> PDFGuiState:
        self.state = replace(self.state, pages_panel_visible=not self.state.pages_panel_visible)
        return self.state

    def toggle_tools_panel(self) -> PDFGuiState:
        self.state = replace(self.state, tools_panel_visible=not self.state.tools_panel_visible)
        return self.state

    def render_source(self) -> bytes | Path | None:
        if not self.state.has_open_pdf:
            return None
        if self.editor.writer is not None:
            stream = BytesIO()
            self.editor.writer.write(stream)
            return stream.getvalue()
        return self.editor.current_pdf_path

    def set_busy(self, is_busy: bool, message: str | None = None) -> PDFGuiState:
        self.state = replace(
            self.state,
            is_busy=is_busy,
            status_message=message or self.state.status_message,
        )
        return self.state

    def refresh_from_editor(self, message: str | None = None) -> PDFGuiState:
        if self.editor.current_pdf_path is None:
            self.state = PDFGuiState(status_message=message or self.state.status_message)
            return self.state

        selected_page = self.state.selected_page or (1 if self.editor.page_count else 0)
        self.state = replace(
            self.state,
            current_file=self.editor.current_pdf_path,
            page_count=self.editor.page_count,
            selected_page=min(selected_page, self.editor.page_count),
            has_unsaved_changes=self.editor.has_unsaved_changes,
            status_message=message or self.state.status_message,
        )
        return self.state

    def _set_zoom(self, zoom: float, mode: ZoomMode | None = None) -> PDFGuiState:
        if not self.state.has_open_pdf:
            return self._set_status("Nenhum PDF aberto.")
        self.state = replace(
            self.state,
            zoom=round(zoom, 2),
            zoom_mode=mode or self.state.zoom_mode,
        )
        return self.state

    def _rotate(self, degrees: int, message: str) -> PDFGuiState:
        if self.state.selected_page < 1:
            return self._set_status("Selecione uma página antes de girar.")
        return self._run_operation(
            message,
            self.editor.rotate_pages,
            [self.state.selected_page],
            degrees=degrees,
        )

    def _all_pages(self) -> list[int]:
        return list(range(1, self.state.page_count + 1))

    def _run_boolean_operation(
        self,
        success_message: str,
        failure_message: str,
        operation: Callable[..., bool],
        *args: object,
        **kwargs: object,
    ) -> PDFGuiState:
        result = operation(*args, **kwargs)
        if not result:
            return self._set_status(failure_message)
        return self.refresh_from_editor(success_message)

    def _run_operation(
        self,
        success_message: str | None,
        operation: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> PDFGuiState:
        try:
            operation(*args, **kwargs)
        except PDFError as exc:
            return self._set_status(f"Erro: {exc}")
        return self.refresh_from_editor(success_message)

    def _require_password(self, password: str) -> None:
        if not password:
            raise PDFValidationError("Informe uma senha.")

    def _set_status(self, message: str) -> PDFGuiState:
        self.state = replace(self.state, status_message=message)
        return self.state
