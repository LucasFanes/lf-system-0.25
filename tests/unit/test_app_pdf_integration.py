from pathlib import Path

from lf_system import config
from lf_system.app import LFSystem


class FakePDFWindow:
    instances: list["FakePDFWindow"] = []

    def __init__(self, pdfs_path: Path) -> None:
        self.pdfs_path = pdfs_path
        self.mainloop_calls = 0
        self.lift_calls = 0
        self.exists = True
        FakePDFWindow.instances.append(self)

    def mainloop(self) -> None:
        self.mainloop_calls += 1
        self.exists = False

    def winfo_exists(self) -> bool:
        return self.exists

    def lift(self) -> None:
        self.lift_calls += 1


def test_main_menu_shows_pdf_editor_option(monkeypatch, tmp_path: Path, capsys) -> None:
    system = _make_system(monkeypatch, tmp_path)

    system.render_tui()

    assert "[D] Editor de PDF" in capsys.readouterr().out


def test_pdf_editor_handler_opens_and_closes_window(monkeypatch, tmp_path: Path) -> None:
    system = _make_system(monkeypatch, tmp_path)
    monkeypatch.setattr("lf_system.pdf_operationsfolder.pdf_gui.PDFEditorWindow", FakePDFWindow)
    FakePDFWindow.instances = []

    system._handle_pdf_editor()

    assert FakePDFWindow.instances[0].pdfs_path == config.PDFS_PATH
    assert FakePDFWindow.instances[0].mainloop_calls == 1
    assert system._pdf_editor_window is None


def test_pdf_editor_handler_reuses_existing_window(monkeypatch, tmp_path: Path) -> None:
    system = _make_system(monkeypatch, tmp_path)
    existing_window = FakePDFWindow(config.PDFS_PATH)
    system._pdf_editor_window = existing_window

    system._handle_pdf_editor()

    assert existing_window.lift_calls == 1


def test_prepare_pages_sorts_and_paginates_directory(monkeypatch, tmp_path: Path) -> None:
    system = _make_system(monkeypatch, tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(config, "ITEMS_PER_PAGE", 2)
    (source / "b.txt").write_text("b", encoding="utf-8")
    (source / "a.txt").write_text("a", encoding="utf-8")
    (source / "c.txt").write_text("c", encoding="utf-8")

    system.prepare_pages(source)

    assert [[path.name for path in page] for page in system.pages] == [
        ["a.txt", "b.txt"],
        ["c.txt"],
    ]


def test_open_folder_handler_changes_current_path(monkeypatch, tmp_path: Path) -> None:
    system = _make_system(monkeypatch, tmp_path)
    target = tmp_path / "Documents"
    target.mkdir()
    system.current_path = tmp_path

    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr("lf_system.app.pyperclip.paste", lambda: "Documents")

    system._handle_open_folder()

    assert system.current_path == target
    assert system.current_page == 0


def _make_system(monkeypatch, tmp_path: Path) -> LFSystem:
    monkeypatch.setattr(config, "SYSTEM_FOLDER", tmp_path / "SISTEMA_LF")
    monkeypatch.setattr(config, "BACKUPS_FOLDER", tmp_path / "SISTEMA_LF" / "Backups")
    monkeypatch.setattr(config, "SPREADSHEETS_FOLDER", tmp_path / "SISTEMA_LF" / "Spreadsheets")
    monkeypatch.setattr(config, "DATA_FOLDER", tmp_path / "SISTEMA_LF" / "Data")
    monkeypatch.setattr(config, "LOGS_FOLDER", tmp_path / "SISTEMA_LF" / "Logs")
    monkeypatch.setattr(config, "PDFS_PATH", tmp_path / "SISTEMA_LF" / "PDFs")
    return LFSystem()
