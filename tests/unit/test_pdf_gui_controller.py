from pathlib import Path

import pytest

from lf_system.pdf_operationsfolder.exceptions import PDFNotOpenError, PDFValidationError
from lf_system.pdf_operationsfolder.pdf_gui_controller import PDFGuiController
from lf_system.pdf_operationsfolder.pdf_gui_state import PDFGuiState


class FakeEditor:
    def __init__(self) -> None:
        self.current_pdf_path: Path | None = None
        self.page_count = 0
        self.has_unsaved_changes = False
        self.closed = False
        self.saved = False
        self.saved_as: Path | None = None
        self.rotations: list[tuple[list[int], int]] = []
        self.writer = None

    def open_pdf(self, pdf_path: str | Path) -> None:
        self.current_pdf_path = Path(pdf_path)
        self.page_count = 3
        self.has_unsaved_changes = False

    def close_pdf(self) -> None:
        self.current_pdf_path = None
        self.page_count = 0
        self.has_unsaved_changes = False
        self.closed = True

    def save(self) -> None:
        if self.current_pdf_path is None:
            raise PDFNotOpenError("No PDF is open.")
        self.saved = True
        self.has_unsaved_changes = False

    def save_as(self, output_path: str | Path) -> None:
        self.saved_as = Path(output_path)

    def rotate_pages(self, pages: list[int], degrees: int = 90) -> None:
        self.rotations.append((pages, degrees))
        self.has_unsaved_changes = True

    def export_pages(self, **kwargs: object) -> Path:
        return Path(kwargs["output_path"])

    def extract_images(self, _output_folder: str | Path) -> int:
        return 2

    def watermark_and_overlay(self, **_kwargs: object) -> bool:
        self.has_unsaved_changes = True
        return True

    def encrypt_pdf(self, _password: str, output_path: str | Path | None = None) -> bool:
        self.has_unsaved_changes = output_path is not None
        return True

    def decrypt_pdf(self, _password: str, output_path: str | Path | None = None) -> bool:
        self.has_unsaved_changes = output_path is not None
        return True


def test_initial_button_states_disable_pdf_operations(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())

    states = controller.state.button_states()

    assert states["open"] == "normal"
    assert states["close"] == "disabled"
    assert states["save"] == "disabled"
    assert states["rotate_right"] == "disabled"


def test_open_pdf_updates_file_page_and_button_state(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())

    state = controller.open_pdf(tmp_path / "documento.pdf")

    assert state.file_name == "documento.pdf"
    assert state.page_count == 3
    assert state.selected_page == 1
    assert state.zoom_mode == "fit_window"
    assert state.button_states()["close"] == "normal"
    assert state.button_states()["save"] == "disabled"


def test_rotate_enables_save_button(tmp_path: Path) -> None:
    editor = FakeEditor()
    controller = PDFGuiController(tmp_path, editor=editor)
    controller.open_pdf(tmp_path / "documento.pdf")

    state = controller.rotate_right()

    assert editor.rotations == [([1], 90)]
    assert state.has_unsaved_changes is True
    assert state.button_states()["save"] == "normal"


def test_save_clears_unsaved_changes(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())
    controller.open_pdf(tmp_path / "documento.pdf")
    controller.rotate_left()

    state = controller.save()

    assert state.has_unsaved_changes is False
    assert state.button_states()["save"] == "disabled"


def test_busy_state_disables_repeated_actions(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())
    controller.open_pdf(tmp_path / "documento.pdf")

    state = controller.set_busy(True)

    assert all(value == "disabled" for value in state.button_states().values())


def test_confirmation_can_cancel_opening_another_pdf(tmp_path: Path) -> None:
    editor = FakeEditor()
    controller = PDFGuiController(tmp_path, editor=editor, confirm=lambda _title, _message: False)
    controller.open_pdf(tmp_path / "primeiro.pdf")
    controller.rotate_right()

    state = controller.open_pdf(tmp_path / "segundo.pdf")

    assert state.file_name == "primeiro.pdf"
    assert state.status_message == "Abertura cancelada."


def test_select_page_validates_bounds(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())
    controller.open_pdf(tmp_path / "documento.pdf")

    with pytest.raises(PDFValidationError):
        controller.select_page(4)


def test_password_is_required_for_crypto_operations(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())
    controller.open_pdf(tmp_path / "documento.pdf")

    with pytest.raises(PDFValidationError, match="senha"):
        controller.encrypt("")


def test_status_labels_for_open_pdf() -> None:
    state = PDFGuiState(
        current_file=Path("arquivo.pdf"),
        page_count=5,
        selected_page=2,
        has_unsaved_changes=True,
    )

    assert state.file_name == "arquivo.pdf"
    assert state.selected_page_label == "Página: 2/5"
    assert state.change_label == "Alterações pendentes"


def test_page_navigation_updates_selected_page(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())
    controller.open_pdf(tmp_path / "documento.pdf")

    assert controller.next_page().selected_page == 2
    assert controller.previous_page().selected_page == 1


def test_page_navigation_respects_first_and_last_page(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())
    controller.open_pdf(tmp_path / "documento.pdf")

    first_state = controller.previous_page()
    controller.select_page(3)
    last_state = controller.next_page()

    assert first_state.selected_page == 1
    assert "primeira" in first_state.status_message
    assert last_state.selected_page == 3
    assert "última" in last_state.status_message


def test_zoom_changes_are_limited(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())
    controller.open_pdf(tmp_path / "documento.pdf")

    assert controller.zoom_in().zoom == 1.25
    assert controller.state.zoom_mode == "manual"
    assert controller.zoom_out().zoom == 1.0

    for _ in range(10):
        controller.zoom_out()
    assert controller.state.zoom == 0.25

    for _ in range(20):
        controller.zoom_in()
    assert controller.state.zoom == 3.0


def test_zoom_modes_update_state(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())
    controller.open_pdf(tmp_path / "documento.pdf")
    controller.zoom_in()

    assert controller.set_zoom_mode("fit_width").zoom_mode == "fit_width"
    assert controller.set_zoom_mode("actual_size").zoom == 1.0
    assert controller.state.zoom_mode == "actual_size"


def test_panel_visibility_can_be_toggled(tmp_path: Path) -> None:
    controller = PDFGuiController(tmp_path, editor=FakeEditor())

    state = controller.toggle_pages_panel()
    assert state.pages_panel_visible is False

    state = controller.toggle_tools_panel()
    assert state.tools_panel_visible is False

    states = state.button_states()
    assert states["toggle_pages"] == "normal"
    assert states["toggle_tools"] == "normal"


def test_rotation_keeps_selected_page_and_refreshes_unsaved_state(tmp_path: Path) -> None:
    editor = FakeEditor()
    controller = PDFGuiController(tmp_path, editor=editor)
    controller.open_pdf(tmp_path / "documento.pdf")
    controller.select_page(2)

    state = controller.rotate_right()

    assert editor.rotations == [([2], 90)]
    assert state.selected_page == 2
    assert state.has_unsaved_changes is True
