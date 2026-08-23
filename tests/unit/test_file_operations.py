from pathlib import Path
from zipfile import ZipFile

from lf_system import file_operations


def test_create_zip_backup_skips_generated_and_virtualenv_paths(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "project"
    backups = tmp_path / "backups"
    backups.mkdir()
    (source / "lf_system").mkdir(parents=True)
    (source / ".venv" / "Scripts").mkdir(parents=True)
    (source / ".pytest_tmp_run").mkdir()
    (source / ".ruff_cache").mkdir()
    (source / "lf_system.egg-info").mkdir()
    (source / "lf_system" / "__pycache__").mkdir()

    (source / "lf_system" / "app.py").write_text("print('ok')", encoding="utf-8")
    (source / ".venv" / "Scripts" / "python.exe").write_text("local", encoding="utf-8")
    (source / ".pytest_tmp_run" / "temp.pdf").write_text("cache", encoding="utf-8")
    (source / ".ruff_cache" / "cache").write_text("cache", encoding="utf-8")
    (source / "lf_system.egg-info" / "PKG-INFO").write_text("cache", encoding="utf-8")
    (source / "lf_system" / "__pycache__" / "app.pyc").write_bytes(b"cache")
    (source / ".coverage").write_text("coverage", encoding="utf-8")

    monkeypatch.setattr(file_operations, "generate_timestamp", lambda: "20260101_000000")
    monkeypatch.setattr(file_operations.pymsgbox, "alert", lambda *args, **kwargs: None)

    assert file_operations.create_zip_backup(source, backups) is True

    zip_path = backups / "Backup_project_20260101_000000.zip"
    with ZipFile(zip_path) as zip_file:
        names = set(zip_file.namelist())

    assert "project/lf_system/app.py" in names
    assert all(".venv" not in name for name in names)
    assert all(".pytest_tmp" not in name for name in names)
    assert all(".ruff_cache" not in name for name in names)
    assert all(".egg-info" not in name for name in names)
    assert all("__pycache__" not in name for name in names)
    assert "project/.coverage" not in names
