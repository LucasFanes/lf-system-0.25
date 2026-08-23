"""SQLite persistence layer for billing accounts and purchases.

Exposes :class:`SQLiteBillingDatabase`, a context manager that keeps the
original dict-like ``database["accounts"]`` API the rest of the system
relies on, while storing data in SQLite tables under the hood. It also
migrates data from the legacy ``shelve``-based database on first use.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from .utils import generate_timestamp


class SQLiteBillingDatabase:
    """SQLite storage that keeps the account dictionary API used by the TUI."""

    def __init__(
        self,
        database_path: Path,
        writeback: bool = False,
    ) -> None:
        self.database_path = Path(database_path)
        self.writeback = writeback
        self.connection: sqlite3.Connection | None = None
        self._accounts_cache: dict[str, Any] | None = None

    def __enter__(self) -> SQLiteBillingDatabase:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.database_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if exc_type is None and self.writeback and self._accounts_cache is not None:
                self._save_accounts(self._accounts_cache)
        finally:
            if self.connection is not None:
                self.connection.close()

    def __contains__(self, key: str) -> bool:
        return key == "accounts"

    def __getitem__(self, key: str) -> dict[str, Any]:
        if key == "accounts":
            return self._load_accounts()
        raise KeyError(key)

    def __setitem__(self, key: str, value: dict[str, Any]) -> None:
        if key != "accounts":
            raise KeyError(key)
        self._save_accounts(value)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "accounts":
            return self._load_accounts()
        return default

    def _create_schema(self) -> None:
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    name TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    billing_items TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nc TEXT NOT NULL UNIQUE,
                    account_name TEXT NOT NULL,
                    item TEXT NOT NULL,
                    price TEXT,
                    date TEXT,
                    FOREIGN KEY (account_name) REFERENCES accounts(name) ON DELETE CASCADE
                )
                """
            )
            self.connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_purchases_account_name
                ON purchases(account_name)
                """
            )

    def _load_accounts(self) -> dict[str, Any]:
        if self._accounts_cache is not None:
            return self._accounts_cache

        accounts: dict[str, Any] = {}
        account_rows = self.connection.execute(
            """
            SELECT name, code, created_at, billing_items
            FROM accounts
            ORDER BY created_at DESC, name
            """
        ).fetchall()

        for account_row in account_rows:
            try:
                billing_items = json.loads(account_row["billing_items"] or "{}")
            except json.JSONDecodeError:
                logging.warning("Invalid billing_items JSON for account %s.", account_row["name"])
                billing_items = {}

            purchase_rows = self.connection.execute(
                """
                SELECT nc, item, price, date
                FROM purchases
                WHERE account_name = ?
                ORDER BY id
                """,
                (account_row["name"],),
            ).fetchall()

            accounts[account_row["name"]] = {
                "code": account_row["code"],
                "created_at": account_row["created_at"],
                "billing_items": billing_items,
                "purchase_history": [
                    {
                        "nc": purchase_row["nc"],
                        "item": purchase_row["item"],
                        "price": purchase_row["price"],
                        "date": purchase_row["date"],
                    }
                    for purchase_row in purchase_rows
                ],
            }

        self._accounts_cache = accounts
        return accounts

    def _save_accounts(self, accounts: dict[str, Any]) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM purchases")
            self.connection.execute("DELETE FROM accounts")

            for account_name, details in accounts.items():
                billing_items = details.get("billing_items", {}) or {}
                self.connection.execute(
                    """
                    INSERT INTO accounts (name, code, created_at, billing_items)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        account_name,
                        details.get("code"),
                        details.get("created_at"),
                        json.dumps(billing_items, ensure_ascii=False),
                    ),
                )

                history = details.get("purchase_history", []) or []
                for purchase in history:
                    nc_code = purchase.get("nc")
                    if not nc_code:
                        continue

                    self.connection.execute(
                        """
                        INSERT OR REPLACE INTO purchases (nc, account_name, item, price, date)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            nc_code,
                            account_name,
                            purchase.get("item", ""),
                            purchase.get("price", ""),
                            purchase.get("date", ""),
                        ),
                    )

        self._accounts_cache = accounts

    def _has_accounts(self) -> bool:
        row = self.connection.execute("SELECT 1 FROM accounts LIMIT 1").fetchone()
        return row is not None

    def roll_back(self) -> bool:
        """Roll back any uncommitted changes to the database."""
        if self.connection is not None:
            self.connection.rollback()
            return True
        return False

    def backup_database(self) -> bool:
        """Create a backup of the current database file."""
        if self.connection is None:
            logging.error("Database connection is not available.")
            return False

        logging.info("Backing up the database...")

        try:
            backup_path = self.database_path.with_name(
                f"{self.database_path.stem}_backup_{generate_timestamp()}"
                f"{self.database_path.suffix}"
            )
            backup_connection = sqlite3.connect(str(backup_path))
            try:
                self.connection.backup(backup_connection)
            finally:
                backup_connection.close()

            logging.info("Database backup completed successfully.")
            return True

        except sqlite3.Error as e:
            logging.error("Error during database backup: %s", e)
            return False
