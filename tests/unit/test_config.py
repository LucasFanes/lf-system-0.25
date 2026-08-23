from pathlib import Path

from lf_system import config


def test_ensure_system_directories_creates_expected_folders(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(config, "BACKUPS_FOLDER", tmp_path / "Backups")
    monkeypatch.setattr(config, "SPREADSHEETS_FOLDER", tmp_path / "Spreadsheets")
    monkeypatch.setattr(config, "DATA_FOLDER", tmp_path / "Data")
    monkeypatch.setattr(config, "LOGS_FOLDER", tmp_path / "Logs")

    config.ensure_system_directories()

    assert config.BACKUPS_FOLDER.is_dir()
    assert config.SPREADSHEETS_FOLDER.is_dir()
    assert config.DATA_FOLDER.is_dir()
    assert config.LOGS_FOLDER.is_dir()


def test_billing_database_path_uses_configured_file_name(tmp_path: Path) -> None:
    assert config.billing_database_path(tmp_path) == tmp_path / config.BILLING_DB_FILENAME
