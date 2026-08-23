from pathlib import Path

from lf_system import utils


def test_show_menu_returns_selected_option(monkeypatch, capsys) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "a")

    assert utils.show_menu("Tools", {"A": "Run"}) == "A"
    assert "TOOLS" in capsys.readouterr().out


def test_show_menu_returns_none_for_cancel(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "s")

    assert utils.show_menu("Tools", {"1": "Run"}) is None


def test_request_path_returns_existing_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(utils.pymsgbox, "prompt", lambda **kwargs: str(tmp_path))

    assert utils.request_path("Path") == tmp_path


def test_request_path_returns_none_when_canceled(monkeypatch) -> None:
    monkeypatch.setattr(utils.pymsgbox, "prompt", lambda **kwargs: None)

    assert utils.request_path("Path") is None
