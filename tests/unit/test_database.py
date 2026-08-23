import sqlite3
from pathlib import Path

from lf_system import database
from lf_system.database import SQLiteBillingDatabase


def test_sqlite_billing_database_persists_accounts_and_purchases(tmp_path: Path) -> None:
    database_path = tmp_path / "billing.sqlite3"
    accounts = {
        "Client A": {
            "code": "C001",
            "created_at": "2026-01-01",
            "billing_items": {"plan": "Pro"},
            "purchase_history": [
                {
                    "nc": "NC001",
                    "item": "Setup",
                    "price": "100",
                    "date": "2026-01-02",
                }
            ],
        }
    }

    with SQLiteBillingDatabase(database_path) as storage:
        storage["accounts"] = accounts

    with SQLiteBillingDatabase(database_path) as storage:
        assert "accounts" in storage
        loaded = storage["accounts"]

    assert loaded["Client A"]["billing_items"] == {"plan": "Pro"}
    assert loaded["Client A"]["purchase_history"][0]["date"] == "2026-01-02"


def test_sqlite_billing_database_writeback_saves_cached_changes(tmp_path: Path) -> None:
    database_path = tmp_path / "billing.sqlite3"

    with SQLiteBillingDatabase(database_path, writeback=True) as storage:
        storage["accounts"] = {}
        storage["accounts"]["Client B"] = {
            "code": "C002",
            "created_at": "2026-01-03",
            "billing_items": {},
            "purchase_history": [],
        }

    with SQLiteBillingDatabase(database_path) as storage:
        assert "Client B" in storage["accounts"]


def test_sqlite_billing_database_backup_creates_readable_copy(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "billing.sqlite3"
    monkeypatch.setattr(database, "generate_timestamp", lambda: "20260101_000000")

    with SQLiteBillingDatabase(database_path) as storage:
        storage["accounts"] = {
            "Client C": {
                "code": "C003",
                "created_at": "2026-01-04",
                "billing_items": {},
                "purchase_history": [],
            }
        }
        assert storage.backup_database() is True

    backup_path = tmp_path / "billing_backup_20260101_000000.sqlite3"
    with sqlite3.connect(backup_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]

    assert count == 1


def test_sqlite_billing_database_reports_rollback_without_connection(tmp_path: Path) -> None:
    storage = SQLiteBillingDatabase(tmp_path / "billing.sqlite3")

    assert storage.roll_back() is False
