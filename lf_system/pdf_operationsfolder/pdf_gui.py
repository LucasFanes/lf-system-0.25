"""Standalone CustomTkinter window for PDF operations."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk  # pyright: ignore[reportMissingImports]

from .exceptions import PDFValidationError
from .pdf_gui_controller import PDFGuiController
from .pdf_gui_state import PDFGuiState
from .pdf_renderer import PDFPageRenderer
from .pdf_view_settings import calculate_zoom


class PDFEditorWindow(ctk.CTk):
    """Independent PDF editor window."""

    def __init__(self, pdfs_path: str | Path | None = None) -> None:
        super().__init__()
        self.title("Editor de PDF - LF System")
        self.geometry("1500x930")
        self.minsize(980, 640)
        self.resizable(True, True)

        base_path = Path(pdfs_path) if pdfs_path else Path.home() / "SISTEMA_LF" / "PDFs"
        self.controller = PDFGuiController(base_path, confirm=self._confirm)
        self.renderer = PDFPageRenderer()
        self.buttons: dict[str, ctk.CTkButton] = {}
        self.page_buttons: list[ctk.CTkButton] = []
        self.page_image: tk.PhotoImage | None = None
        self.is_fullscreen = False
        self._render_after_id: str | None = None

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._build_layout()
        self._bind_shortcuts()
        self._render_state()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, minsize=170, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, minsize=210, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_page_panel()
        self._build_document_area()
        self._build_tools_panel()
        self._build_status_bar()
        self._apply_panel_visibility()

    def _build_top_bar(self) -> None:
        top_bar = ctk.CTkFrame(self, height=56, corner_radius=0)
        top_bar.grid(row=0, column=0, columnspan=3, sticky="ew")
        top_bar.grid_columnconfigure(2, weight=1)

        self._add_button(top_bar, "open", "Abrir", self._open_file, 0, 0)
        self._add_button(top_bar, "save", "Salvar", self._save, 0, 1)
        self._add_button(top_bar, "save_as", "Salvar como", self._save_as, 0, 2)
        self._add_button(top_bar, "toggle_pages", "Páginas", self._toggle_pages_panel, 0, 3)
        self._add_button(top_bar, "toggle_tools", "Ferramentas", self._toggle_tools_panel, 0, 4)
        self._add_button(top_bar, "fullscreen", "Tela cheia", self._toggle_fullscreen, 0, 5)

        self.file_label = ctk.CTkLabel(top_bar, text="Nenhum arquivo", anchor="e")
        self.file_label.grid(row=0, column=6, padx=16, pady=10, sticky="e")

    def _build_page_panel(self) -> None:
        panel = ctk.CTkFrame(self, width=170, corner_radius=0)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_propagate(False)
        panel.grid_rowconfigure(1, weight=1)
        self.page_panel = panel

        ctk.CTkLabel(panel, text="Páginas", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=14, pady=(14, 8), sticky="w"
        )
        self.pages_frame = ctk.CTkScrollableFrame(panel, width=145)
        self.pages_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _build_document_area(self) -> None:
        area = ctk.CTkFrame(self, corner_radius=0)
        area.grid(row=1, column=1, sticky="nsew")
        area.grid_columnconfigure(0, weight=1)
        area.grid_rowconfigure(2, weight=1)

        self.document_title = ctk.CTkLabel(
            area,
            text="Área do documento",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.document_title.grid(row=0, column=0, padx=20, pady=(18, 6), sticky="w")

        viewer_controls = ctk.CTkFrame(area, corner_radius=0)
        viewer_controls.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")
        self._add_button(
            viewer_controls, "previous_page", "Página anterior", self._previous_page, 0, 0
        )
        self._add_button(viewer_controls, "next_page", "Próxima página", self._next_page, 0, 1)
        self._add_button(viewer_controls, "zoom_out", "Zoom -", self._zoom_out, 0, 2)
        self._add_button(viewer_controls, "zoom_in", "Zoom +", self._zoom_in, 0, 3)
        self._add_button(
            viewer_controls, "fit_window", "Ajustar à janela", self._fit_window, 0, 4
        )
        self._add_button(
            viewer_controls, "fit_width", "Ajustar à largura", self._fit_width, 0, 5
        )
        self._add_button(viewer_controls, "actual_size", "Tamanho real", self._actual_size, 0, 6)
        self._add_button(viewer_controls, "manual_zoom", "Zoom manual", self._manual_zoom, 0, 7)

        self.viewer_frame = ctk.CTkScrollableFrame(area)
        self.viewer_frame.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self.viewer_frame.grid_columnconfigure(0, weight=1)
        self.viewer_frame.bind("<Configure>", self._schedule_render)
        self.document_label = tk.Label(
            self.viewer_frame,
            text="Abra um PDF para visualizar a página selecionada.",
            compound="top",
            background="#f5f5f5",
        )
        self.document_label.grid(row=0, column=0, padx=8, pady=8)

    def _build_tools_panel(self) -> None:
        panel = ctk.CTkFrame(self, width=210, corner_radius=0)
        panel.grid(row=1, column=2, sticky="nsew")
        panel.grid_propagate(False)
        self.tools_panel = panel

        ctk.CTkLabel(panel, text="Ferramentas", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=14, pady=(14, 8), sticky="w"
        )

        tools: list[tuple[str, str, Callable[[], None]]] = [
            ("close", "Fechar", self._close_file),
            ("rotate_left", "Girar à esquerda", self._rotate_left),
            ("rotate_right", "Girar à direita", self._rotate_right),
            ("extract_pages", "Extrair páginas", self._extract_pages),
            ("extract_images", "Extrair imagens", self._extract_images),
            ("watermark", "Aplicar marca-d'água", self._apply_watermark),
            ("encrypt", "Criptografar", self._encrypt),
            ("decrypt", "Descriptografar", self._decrypt),
        ]
        for row, (key, label, command) in enumerate(tools, start=1):
            self._add_button(panel, key, label, command, row, 0, sticky="ew")

    def _build_status_bar(self) -> None:
        status_bar = ctk.CTkFrame(self, height=34, corner_radius=0)
        status_bar.grid(row=2, column=0, columnspan=3, sticky="ew")
        status_bar.grid_columnconfigure(3, weight=1)

        self.pages_label = ctk.CTkLabel(status_bar, text="Páginas: 0")
        self.pages_label.grid(row=0, column=0, padx=12, pady=6, sticky="w")
        self.selected_page_label = ctk.CTkLabel(status_bar, text="Página: -")
        self.selected_page_label.grid(row=0, column=1, padx=12, pady=6, sticky="w")
        self.changes_label = ctk.CTkLabel(status_bar, text="Sem alterações")
        self.changes_label.grid(row=0, column=2, padx=12, pady=6, sticky="w")
        self.status_label = ctk.CTkLabel(status_bar, text="Nenhum PDF aberto.", anchor="e")
        self.status_label.grid(row=0, column=3, padx=12, pady=6, sticky="e")

    def _add_button(
        self,
        parent: ctk.CTkFrame,
        key: str,
        text: str,
        command: Callable[[], None],
        row: int,
        column: int,
        sticky: str = "w",
    ) -> None:
        button = ctk.CTkButton(parent, text=text, command=lambda: self._guarded(command))
        button.grid(row=row, column=column, padx=8, pady=8, sticky=sticky)
        self.buttons[key] = button

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-o>", lambda _event: self._open_file())
        self.bind("<Control-s>", lambda _event: self._save())
        self.bind("<Control-Shift-S>", lambda _event: self._save_as())
        self.bind("<F11>", lambda _event: self._toggle_fullscreen())
        self.bind("<Escape>", lambda _event: self._exit_fullscreen())

    def _guarded(self, action: Callable[[], None]) -> None:
        if self.controller.state.is_busy:
            return
        self.controller.set_busy(True, "Operação em andamento...")
        self._render_state()
        try:
            action()
        except PDFValidationError as exc:
            self._show_error(str(exc))
        finally:
            self.controller.set_busy(False)
            self._render_state()

    def _open_file(self) -> None:
        file_name = filedialog.askopenfilename(
            title="Abrir PDF",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if not file_name:
            self._show_cancel("Abertura cancelada.")
            return

        self.controller.open_pdf(file_name)
        self._show_success("PDF aberto com sucesso.")

    def _close_file(self) -> None:
        state = self.controller.close_pdf()
        if state.has_open_pdf:
            self._show_cancel(state.status_message)
            return
        self._show_success("PDF fechado.")

    def _save(self) -> None:
        if not self.controller.state.can_save:
            self._show_cancel("Não há alterações para salvar.")
            return
        self.controller.save()
        self._show_success("PDF salvo.")

    def _save_as(self) -> None:
        output_path = filedialog.asksaveasfilename(
            title="Salvar PDF como",
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if not output_path:
            self._show_cancel("Salvar como cancelado.")
            return
        self.controller.save_as(output_path)
        self._show_success("PDF salvo como novo arquivo.")

    def _rotate_left(self) -> None:
        self.controller.rotate_left()
        self._show_success("Página girada à esquerda.")

    def _rotate_right(self) -> None:
        self.controller.rotate_right()
        self._show_success("Página girada à direita.")

    def _previous_page(self) -> None:
        self.controller.previous_page()
        self._render_state()

    def _next_page(self) -> None:
        self.controller.next_page()
        self._render_state()

    def _zoom_out(self) -> None:
        self.controller.zoom_out()
        self._render_state()

    def _zoom_in(self) -> None:
        self.controller.zoom_in()
        self._render_state()

    def _fit_window(self) -> None:
        self.controller.set_zoom_mode("fit_window")
        self._render_state()

    def _fit_width(self) -> None:
        self.controller.set_zoom_mode("fit_width")
        self._render_state()

    def _actual_size(self) -> None:
        self.controller.set_zoom_mode("actual_size")
        self._render_state()

    def _manual_zoom(self) -> None:
        self.controller.set_zoom_mode("manual")
        self._render_state()

    def _toggle_pages_panel(self) -> None:
        self.controller.toggle_pages_panel()
        self._render_state()

    def _toggle_tools_panel(self) -> None:
        self.controller.toggle_tools_panel()
        self._render_state()

    def _toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        self._render_state()

    def _exit_fullscreen(self) -> None:
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)
            self._render_state()

    def _extract_pages(self) -> None:
        pages = self._ask_pages("Páginas para extrair")
        if pages is None:
            self._show_cancel("Extração cancelada.")
            return
        output_path = filedialog.asksaveasfilename(
            title="Salvar páginas extraídas",
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if not output_path:
            self._show_cancel("Extração cancelada.")
            return
        self.controller.extract_pages(pages, output_path)
        self._show_success("Páginas extraídas com sucesso.")

    def _extract_images(self) -> None:
        output_folder = filedialog.askdirectory(title="Pasta para imagens extraídas")
        if not output_folder:
            self._show_cancel("Extração de imagens cancelada.")
            return
        self.controller.extract_images(output_folder)
        self._show_success(self.controller.state.status_message)

    def _apply_watermark(self) -> None:
        watermark_path = filedialog.askopenfilename(
            title="Selecionar marca-d'água",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if not watermark_path:
            self._show_cancel("Marca-d'água cancelada.")
            return
        output_path = filedialog.asksaveasfilename(
            title="Salvar PDF com marca-d'água",
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if not output_path:
            self._show_cancel("Marca-d'água cancelada.")
            return
        self.controller.apply_watermark(watermark_path, output_path)
        self._show_success("Marca-d'água aplicada com sucesso.")

    def _encrypt(self) -> None:
        password = simpledialog.askstring("Criptografar", "Senha:", show="*")
        if password is None:
            self._show_cancel("Criptografia cancelada.")
            return
        output_path = self._ask_optional_output("Salvar PDF criptografado")
        self.controller.encrypt(password, output_path=output_path)
        self._show_success(self.controller.state.status_message)

    def _decrypt(self) -> None:
        password = simpledialog.askstring("Descriptografar", "Senha:", show="*")
        if password is None:
            self._show_cancel("Descriptografia cancelada.")
            return
        output_path = self._ask_optional_output("Salvar PDF descriptografado")
        self.controller.decrypt(password, output_path=output_path)
        self._show_success(self.controller.state.status_message)

    def _ask_optional_output(self, title: str) -> str | None:
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
        ) or None

    def _ask_pages(self, title: str) -> list[int] | None:
        raw_pages = simpledialog.askstring(title, "Informe as páginas, separadas por vírgula:")
        if raw_pages is None:
            return None
        try:
            return [int(page.strip()) for page in raw_pages.split(",") if page.strip()]
        except ValueError as exc:
            raise PDFValidationError("Informe apenas números de páginas.") from exc

    def _render_state(self) -> None:
        state = self.controller.state
        self._render_buttons(state)
        self._render_pages(state)
        self.file_label.configure(text=state.file_name)
        self.pages_label.configure(text=f"Páginas: {state.page_count}")
        self.selected_page_label.configure(text=state.selected_page_label)
        self.changes_label.configure(text=state.change_label)
        self.status_label.configure(text=f"{state.status_message} | {state.zoom_label}")
        self._apply_panel_visibility()
        self._render_document(state)

    def _render_buttons(self, state: PDFGuiState) -> None:
        button_states = state.button_states()
        for key, button in self.buttons.items():
            button.configure(state=button_states[key])

    def _render_pages(self, state: PDFGuiState) -> None:
        for button in self.page_buttons:
            button.destroy()
        self.page_buttons = []

        for page_number in range(1, state.page_count + 1):
            button = ctk.CTkButton(
                self.pages_frame,
                text=f"Página {page_number}",
                command=lambda number=page_number: self._select_page(number),
                fg_color="#1f6aa5" if page_number == state.selected_page else "transparent",
                border_width=1,
            )
            button.grid(row=page_number - 1, column=0, padx=8, pady=5, sticky="ew")
            self.page_buttons.append(button)

    def _apply_panel_visibility(self) -> None:
        state = self.controller.state
        if state.pages_panel_visible:
            self.page_panel.grid()
        else:
            self.page_panel.grid_remove()

        if state.tools_panel_visible:
            self.tools_panel.grid()
        else:
            self.tools_panel.grid_remove()

    def _select_page(self, page_number: int) -> None:
        self.controller.select_page(page_number)
        self._render_state()

    def _render_document(self, state: PDFGuiState) -> None:
        source = self.controller.render_source()
        if source is None or state.selected_page < 1:
            self.page_image = None
            self.document_label.configure(
                image="",
                text="Abra um PDF para visualizar a página selecionada.",
            )
            return

        try:
            page_width, page_height = self.renderer.page_size(source, state.selected_page)
            render_zoom = self._render_zoom(state, page_width, page_height)
            rendered = self.renderer.render_page(source, state.selected_page, render_zoom)
        except Exception as exc:
            self.page_image = None
            self.document_label.configure(image="", text="Não foi possível renderizar a página.")
            self.status_label.configure(text=f"Erro de renderização: {exc}")
            return

        self.page_image = tk.PhotoImage(data=rendered.image_data)
        self.document_label.configure(image=self.page_image, text="")

    def _render_zoom(self, state: PDFGuiState, page_width: float, page_height: float) -> float:
        viewport_width = max(1, self.viewer_frame.winfo_width())
        viewport_height = max(1, self.viewer_frame.winfo_height())
        render_zoom = calculate_zoom(
            state.zoom_mode,
            page_width,
            page_height,
            viewport_width,
            viewport_height,
            state.zoom,
        )
        if render_zoom != state.zoom:
            self.controller.set_effective_zoom(render_zoom)
        return render_zoom

    def _schedule_render(self, _event: tk.Event | None = None) -> None:
        if self._render_after_id is not None:
            self.after_cancel(self._render_after_id)
        self._render_after_id = self.after(120, self._render_scheduled_state)

    def _render_scheduled_state(self) -> None:
        self._render_after_id = None
        self._render_state()

    def _confirm(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)

    def _show_success(self, message: str) -> None:
        self.controller.refresh_from_editor(message)
        self._render_state()

    def _show_error(self, message: str) -> None:
        self.controller.set_busy(False, f"Erro: {message}")
        messagebox.showerror("Erro", message)

    def _show_cancel(self, message: str) -> None:
        self.controller.set_busy(False, message)
        self._render_state()


def main() -> None:
    app = PDFEditorWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
