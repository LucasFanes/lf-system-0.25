"""LF System TUI: terminal interface and top-level menu routing."""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pymsgbox
import pyperclip

from . import config, file_operations, utils
from .billing import BillingMonitor, BillingService
from .spreadsheet import SpreadsheetExport


class LFSystem:
    """Main class for the TUI ecosystem and unified operational control."""

    def __init__(self) -> None:
        self.drive = config.HOME_DIR
        self.system_folder = config.SYSTEM_FOLDER
        self.backups_folder = config.BACKUPS_FOLDER
        self.spreadsheets_folder = config.SPREADSHEETS_FOLDER
        self.data_folder = config.DATA_FOLDER

        self.current_path = Path.cwd()
        self.pages: list[Any] = []
        self.current_page = 0
        self._pdf_editor_window: Any | None = None

        config.ensure_system_directories()

    def modern_loading_screen(self) -> None:
        """Modern terminal loading bar."""
        utils.clear_screen()
        bar_width = 40
        print("\n" * 2)
        print(" INITIALIZING LF OPERATIONAL ECOSYSTEM ".center(65, "="))
        print("\n Mapping local buffers and starting core modules...\n")

        for index in range(bar_width + 1):
            percent = int((index / bar_width) * 100)
            filled = "#" * index
            empty = "-" * (bar_width - index)
            print(f"\r Syncing tables: |{filled}{empty}| {percent}% Complete", end="", flush=True)
            time.sleep(0.04)

        print("\n\n" + " INTEGRATED ENVIRONMENT READY ".center(65, "="))
        time.sleep(0.8)
        utils.clear_screen()

    def prepare_pages(self, target_path: Path | None = None) -> None:
        """Prepare paginated directory entries. Accepts an alternate target path."""
        try:
            target = target_path if target_path is not None else self.current_path
            items = sorted([path for path in target.glob("*")], key=lambda path: path.name.lower())
            self.pages = [
                items[i : i + config.ITEMS_PER_PAGE]
                for i in range(0, len(items), config.ITEMS_PER_PAGE)
            ]
        except Exception:
            self.pages = []

    def render_tui(self, custom_menu: str | None = None, custom_path: Path | None = None) -> None:
        """Render the base TUI. Optional arguments support the spreadsheet module."""
        utils.clear_screen()
        display_address = custom_path if custom_path is not None else self.current_path

        print(f" FILE OPERATIONS LF | Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f" Active Path: {display_address}")
        print(f" Item Page: {self.current_page + 1}/{max(1, len(self.pages))}")
        print("=" * config.TUI_DIVIDER_WIDTH)

        if not self.pages:
            print("   (Directory is empty or scan permissions are unavailable)")
        else:
            if self.current_page >= len(self.pages):
                self.current_page = 0
            for file_path in self.pages[self.current_page]:
                item_type = "[DIR]" if file_path.is_dir() else "[FILE]"
                print(f"  {item_type} {file_path.name}")

        print("=" * config.TUI_DIVIDER_WIDTH)
        if custom_menu:
            print(f" {custom_menu}")
        else:
            print(
                " [1] Next Page   | [2] Previous Page | [B] Parent Folder | "
                "[S] Zip Item (Clipboard)"
            )
            print(
                " [G] Open Folder | [C] Backup        | [F] Copy Items    | "
                "[E] Billing | [P] Create Excel"
            )
            print(" [D] Editor de PDF")
            print(" [ESC] End Session")
        print("=" * config.TUI_DIVIDER_WIDTH)

    def interface_loop(self) -> None:
        while True:
            self.prepare_pages(self.current_path)
            self.render_tui()

            command = input("Enter a panel command and press Enter: ").strip().lower()

            if command == "1" and self.current_page < len(self.pages) - 1:
                self.current_page += 1
            elif command == "2" and self.current_page > 0:
                self.current_page -= 1
            elif command == "b":
                self.current_path = self.current_path.parent
                self.current_page = 0
            elif command == "esc":
                print("\nDisconnecting from local storage and closing processes safely...")
                time.sleep(0.6)
                sys.exit()

            elif command == "g":
                self._handle_open_folder()
            elif command == "s":
                self._handle_zip_clipboard_item()
            elif command == "c":
                self._handle_manual_backup()
            elif command == "f":
                self._handle_copy_items()
            elif command == "e":
                self._handle_billing_menu()
            elif command == "p":
                self._handle_spreadsheet_menu()
            elif command == "d":
                self._handle_pdf_editor()

    def _handle_open_folder(self) -> None:
        print("\n>> OPEN FOLDER MODE: Copy the Windows folder name...")
        input("Press Enter here after copying the name:")
        clipboard_content = pyperclip.paste().strip()
        target = self.current_path / clipboard_content
        if target.exists() and target.is_dir():
            self.current_path = target
            self.current_page = 0
        else:
            print("Target directory was not found in the active path.")
            time.sleep(1.5)

    def _handle_zip_clipboard_item(self) -> None:
        print("\n>> ZIP MODE: Copy the exact file name to compress...")
        input("Press Enter here after copying the name:")
        clipboard_content = pyperclip.paste().strip()
        target = self.current_path / clipboard_content
        if target.exists():
            if target.is_file():
                file_operations.create_zip_backup(target, self.backups_folder)
            else:
                print("The target is a folder. Use the dedicated [C] tool.")
                time.sleep(1.5)

    def _handle_manual_backup(self) -> None:
        user_input = utils.request_path("Enter the full path of the item to back up:")
        if user_input:
            file_operations.create_zip_backup(user_input, self.backups_folder)

    def _handle_copy_items(self) -> None:
        choice = utils.show_menu(
            "File Replication Module",
            {
                "1": "Direct isolated copy (single item)",
                "2": "Grouped smart copy (file tree)",
            },
        )
        if choice:
            source = utils.request_path("SOURCE path:")
            destination = utils.request_path("DESTINATION path:")
            if source and destination:
                if choice == "1":
                    file_operations.copy_single_item(source, destination)
                elif choice == "2":
                    file_operations.copy_folder_contents(source, destination)

    def _handle_billing_menu(self) -> None:
        billing_service = BillingService(self.data_folder)
        billing_monitor = BillingMonitor(billing_service)

        while True:
            option = utils.show_menu(
                "Audit and Accounting Panel",
                {
                    "1": "Register New Account",
                    "2": "Show Account Metadata",
                    "3": "Update Internal Records",
                    "4": "Monitor Database",
                    "5": "Post Purchase Entry",
                    "6": "Reverse Entry by NC Code",
                },
            )
            if option == "1":
                billing_service.create_billing_account()
            elif option == "2":
                billing_service.show_account_details()
            elif option == "3":
                billing_service.edit_account()
            elif option == "4":
                self._handle_billing_monitor_menu(billing_monitor)
            elif option == "5":
                self._handle_add_purchase(billing_service)
            elif option == "6":
                billing_service.delete_purchase()
            else:
                break

    def _handle_billing_monitor_menu(self, billing_monitor: BillingMonitor) -> None:
        sub_option = utils.show_menu(
            "Monitor Filter Selection",
            {"1": "Active Customers", "2": "General Purchase History"},
        )
        if sub_option == "1":
            billing_monitor.monitor_customers()
        elif sub_option == "2":
            billing_monitor.monitor_purchases()

    def _handle_add_purchase(self, billing_service: BillingService) -> None:
        account_name = pymsgbox.prompt("Linked Account Name:")
        item = pymsgbox.prompt("Purchased Item:")
        price = pymsgbox.prompt("Item Value:")
        if account_name and item and price:
            billing_service.add_purchase(account_name.strip(), item.strip(), price.strip())

    def _handle_spreadsheet_menu(self) -> None:
        spreadsheet_export = SpreadsheetExport(self.spreadsheets_folder, self.data_folder)
        spreadsheet_export.spreadsheet_interface_loop(self)

    def _handle_pdf_editor(self) -> None:
        config.PDFS_PATH.mkdir(parents=True, exist_ok=True)

        if self._is_pdf_editor_open():
            self._pdf_editor_window.lift()
            return

        from .pdf_operationsfolder.pdf_gui import PDFEditorWindow

        self._pdf_editor_window = PDFEditorWindow(config.PDFS_PATH)
        try:
            self._pdf_editor_window.mainloop()
        finally:
            self._pdf_editor_window = None

    def _is_pdf_editor_open(self) -> bool:
        if self._pdf_editor_window is None:
            return False
        try:
            return bool(self._pdf_editor_window.winfo_exists())
        except Exception:
            return False
