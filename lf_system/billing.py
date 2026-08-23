"""Billing business logic: account CRUD, purchases and account monitoring."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pymsgbox

from . import config
from .database import SQLiteBillingDatabase
from .utils import clear_screen, generate_timestamp


class BillingService:
    """Account and purchase CRUD operations backed by SQLite."""

    def __init__(self, data_folder: Path | None = None) -> None:
        self.data_folder = Path(data_folder) if data_folder else config.DATA_FOLDER
        self.database_path = config.billing_database_path(self.data_folder)

    def open_database(self, writeback: bool = False) -> SQLiteBillingDatabase:
        return SQLiteBillingDatabase(
            self.database_path,
            writeback=writeback,
        )

    @staticmethod
    def get_accounts(database: SQLiteBillingDatabase) -> dict[str, Any]:
        return database.get("accounts", {})

    @staticmethod
    def ensure_accounts(database: SQLiteBillingDatabase) -> dict[str, Any]:
        if "accounts" not in database:
            database["accounts"] = {}
        return database["accounts"]

    def create_billing_account(self) -> None:
        try:
            with self.open_database(writeback=True) as database:
                all_accounts = self.ensure_accounts(database)

                account_name = pymsgbox.prompt(
                    "New account name (example: Cash_A):",
                    "Create Account",
                )
                if account_name and account_name.strip():
                    account_name = account_name.strip()
                    if account_name in all_accounts:
                        pymsgbox.alert("This account already exists.", "Error")
                        return

                    highest_id = -1
                    for account in all_accounts.values():
                        code = account.get("code", "LF0")
                        number = int(code.replace("LF", ""))
                        highest_id = max(highest_id, number)

                    new_code = f"LF{highest_id + 1}"
                    all_accounts[account_name] = {
                        "code": new_code,
                        "created_at": generate_timestamp(),
                        "billing_items": {
                            "age": "Not provided",
                            "customer_name": "Not provided",
                            "customer_address": "Not provided",
                        },
                        "purchase_history": [],
                    }
                    database["accounts"] = all_accounts
                    pymsgbox.alert(
                        f"Account '{account_name}' created with code {new_code}.",
                        "Success",
                    )
        except Exception as exc:
            logging.error("Create account error: %s", exc, exc_info=True)

    def show_account_details(self) -> None:
        try:
            with self.open_database() as database:
                all_accounts = self.get_accounts(database)
                selected_account = pymsgbox.prompt("Enter the account name:")
                if selected_account in all_accounts:
                    details = all_accounts[selected_account]
                    billing_items = details.get("billing_items", {})
                    items = "\n".join([f"{key}: {value}" for key, value in billing_items.items()])
                    info = (
                        f"Account: {selected_account}\n"
                        f"Code: {details.get('code')}\n"
                        f"Created: {details.get('created_at')}\n\n"
                        f"Fields:\n{items}"
                    )
                    pymsgbox.alert(info, "Details")
                else:
                    pymsgbox.alert("Account not found.", "Error")
        except Exception as exc:
            logging.error("Account details error: %s", exc, exc_info=True)

    def add_purchase(self, account_name: str, item: str, price: str) -> None:
        try:
            with self.open_database(writeback=True) as database:
                all_accounts = self.ensure_accounts(database)

                if account_name in all_accounts:
                    highest_nc = -1
                    for account in all_accounts.values():
                        history = account.get("purchase_history", [])
                        for purchase in history:
                            number = int(purchase["nc"].replace("NC", ""))
                            highest_nc = max(highest_nc, number)

                    new_nc = f"NC{highest_nc + 1}"
                    all_accounts[account_name].setdefault("purchase_history", []).append(
                        {
                            "nc": new_nc,
                            "item": item,
                            "price": price,
                            "date": generate_timestamp(),
                        }
                    )
                    database["accounts"] = all_accounts
                    pymsgbox.alert(f"Purchase posted. Code: {new_nc}", "Success")
                else:
                    pymsgbox.alert("Account is not registered.", "Error")
        except Exception as exc:
            logging.error("Add purchase error: %s", exc, exc_info=True)

    def delete_purchase(self) -> None:
        try:
            with self.open_database(writeback=True) as database:
                all_accounts = self.ensure_accounts(database)
                target = pymsgbox.prompt("Enter the NC code for the item to delete:")
                if not target:
                    return
                target = target.strip().upper()

                found = False
                for details in all_accounts.values():
                    history = details.get("purchase_history", [])
                    for purchase in list(history):
                        if purchase.get("nc") == target:
                            confirmation = pymsgbox.prompt(
                                f"Type DELETE to confirm deletion of {purchase['item']}:"
                            )
                            if confirmation == "DELETE":
                                history.remove(purchase)
                                details["purchase_history"] = history
                                pymsgbox.alert("Item removed.", "Success")
                                found = True
                            break

                database["accounts"] = all_accounts
                if not found:
                    pymsgbox.alert("Code not found.", "Error")
        except Exception as exc:
            logging.error("Delete purchase error: %s", exc, exc_info=True)

    def edit_account(self) -> None:
        try:
            with self.open_database(writeback=True) as database:
                all_accounts = self.ensure_accounts(database)
                selected_account = pymsgbox.prompt("Account to update:")
                if selected_account in all_accounts:
                    items = all_accounts[selected_account].setdefault("billing_items", {})
                    keys = list(items.keys())

                    while True:
                        clear_screen()
                        print(f"--- EDIT ACCOUNT: {selected_account} ---")
                        for index, key in enumerate(keys):
                            print(f" [{index}] {key.upper()}: {items[key]}")
                        print(" [S] Exit")

                        option = input("\nChoose the field index to update: ").strip()
                        if option.lower() == "s":
                            break
                        if option.isdigit() and int(option) < len(keys):
                            target_key = keys[int(option)]
                            new_value = pymsgbox.prompt(
                                f"New value for {target_key}:",
                                default=items[target_key],
                            )
                            if new_value is not None:
                                items[target_key] = new_value.strip()

                    database["accounts"] = all_accounts
                else:
                    pymsgbox.alert("Account does not exist.", "Error")
        except Exception as exc:
            logging.error("Edit account error: %s", exc, exc_info=True)


class BillingMonitor:
    """Read-only, paginated monitoring views over billing accounts."""

    def __init__(self, billing_service: BillingService) -> None:
        self.billing_service = billing_service

    def monitor_customers(self) -> None:
        logging.info("Customer monitoring started.")
        try:
            with self.billing_service.open_database() as database:
                all_accounts = self.billing_service.get_accounts(database)
                if not all_accounts:
                    self._empty_screen("Customers")
                    return

                ordered_accounts = sorted(
                    list(all_accounts.items()),
                    key=lambda item: item[1].get("created_at", ""),
                    reverse=True,
                )
                pages = [ordered_accounts[i : i + 10] for i in range(0, len(ordered_accounts), 10)]
                current_page = 0

                while True:
                    clear_screen()
                    print("--- CUSTOMER MONITOR ---")
                    print(f"Page: {current_page + 1}/{max(1, len(pages))}\n" + "-" * 60)

                    for account_name, details in pages[current_page]:
                        created = details.get("created_at", "")
                        billing_items = details.get("billing_items", {})
                        customer = billing_items.get("customer_name", "N/A")
                        code = details.get("code", "N/A")
                        print(
                            f"[{code}] Account: {account_name:<12} | "
                            f"Customer: {customer:<18} | Created: {created}"
                        )

                    print("-" * 60)
                    print(" [1] Next Page | [2] Previous Page | [S] Back")
                    command = input("Command: ").strip().lower()
                    if command == "1" and current_page < len(pages) - 1:
                        current_page += 1
                    elif command == "2" and current_page > 0:
                        current_page -= 1
                    elif command == "s":
                        break
        except Exception as exc:
            logging.error("Customer monitor error: %s", exc, exc_info=True)

    def monitor_purchases(self) -> None:
        logging.info("Global purchase monitoring started.")
        try:
            with self.billing_service.open_database() as database:
                all_accounts = self.billing_service.get_accounts(database)
                if not all_accounts:
                    self._empty_screen("Purchases")
                    return

                global_purchases = []
                for account_name, details in all_accounts.items():
                    history = details.get("purchase_history", [])
                    for purchase in history:
                        global_purchases.append(
                            {
                                "nc": purchase.get("nc", "N/NC"),
                                "account": account_name,
                                "item": purchase["item"],
                                "price": purchase.get("price", purchase.get("preco")),
                                "date": purchase.get("date", purchase.get("data")),
                            }
                        )

                if not global_purchases:
                    self._empty_screen("Purchases")
                    return

                global_purchases = sorted(
                    global_purchases,
                    key=lambda item: item["date"],
                    reverse=True,
                )
                pages = [global_purchases[i : i + 10] for i in range(0, len(global_purchases), 10)]
                current_page = 0

                while True:
                    clear_screen()
                    print("--- GLOBAL PURCHASE HISTORY ---")
                    print(f"Page: {current_page + 1}/{max(1, len(pages))}\n" + "-" * 70)

                    for purchase in pages[current_page]:
                        print(
                            f"[{purchase['nc']:<5}] Item: {purchase['item']:<15} | "
                            f"$ {purchase['price']:<8} | Account: {purchase['account']:<10} | "
                            f"Date: {purchase['date']}"
                        )

                    print("-" * 70)
                    print(" [1] Next Page | [2] Previous Page | [S] Back")
                    command = input("Command: ").strip().lower()
                    if command == "1" and current_page < len(pages) - 1:
                        current_page += 1
                    elif command == "2" and current_page > 0:
                        current_page -= 1
                    elif command == "s":
                        break
        except Exception as exc:
            logging.error("Purchase monitor error: %s", exc, exc_info=True)

    @staticmethod
    def _empty_screen(item_type: str) -> None:
        clear_screen()
        print(f"--- Empty {item_type} History ---")
        input("\nNo records found. Press Enter...")
