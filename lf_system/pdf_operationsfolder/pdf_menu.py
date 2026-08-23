"""Interactive text-based front end for the LF System: PDFReader.

This module owns all user interaction (prompts, confirmations, printed
output). It holds no PDF-editing logic of its own — it only calls into
:class:`PDFEditor` — so a future TUI, GUI (own viewer), or API can be built
the same way, reusing :class:`PDFEditor` unchanged.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .pdf_editor import PDFAdvancedEditor

logger = logging.getLogger(__name__)


class PDFMenu:
    """Command-line menu that drives a :class:`PDFAdvancedEditor` instance."""

    def __init__(self, pdfs_path: Path, writeback: bool = False) -> None:
        self.editor = PDFAdvancedEditor(pdfs_path, writeback)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Open a PDF, then present the main menu loop until the user quits."""
        if not self._open_pdf_flow():
            return

        actions = {
            "1": self.rotate_pages_flow,
            "2": self.read_text_flow,
            "3": self.extract_images_flow,
            "4": self.export_pages_flow,
            "5": self.save_flow,
            "6": self.encrypt_pdf_flow,
            "7": self.decrypt_pdf_flow,
            "8": self.watermark_flow,
            "o": self._open_pdf_flow,
        }

        while True:
            print(
                "\n".join(
                    [
                        "",
                        f"Current file: {self.editor.current_pdf_path}",
                        "1) Rotate pages",
                        "2) Read text",
                        "3) Extract images",
                        "4) Export a page range as a new PDF",
                        "5) Save",
                        "6) Encrypt PDF",
                        "7) Decrypt PDF",
                        "8) Add watermark/overlay",
                        "o) Open a different PDF",
                        "q) Quit",
                    ]
                )
            )
            choice = input("Choose an option: ").strip().lower()

            if choice == "q":
                return

            action = actions.get(choice)
            if action is None:
                print("Invalid option.")
                continue

            action()

    # ------------------------------------------------------------------
    # Opening a PDF
    # ------------------------------------------------------------------
    def _open_pdf_flow(self) -> bool:
        """Let the user pick a PDF (from ``pdfs_path`` or a typed path).

        Returns True once a PDF has been successfully opened, False if the
        user cancelled (only relevant on first entry into :meth:`run`).
        """
        while True:
            available = self.editor.list_available_pdfs()

            if available:
                print("\nAvailable PDFs:")
                for index, path in enumerate(available, start=1):
                    print(f"  {index}) {path.name}")

            raw = input(
                "Enter the number of a PDF above, a full path, or 'exit' to cancel: "
            ).strip()

            if raw.lower() == "exit":
                return self.editor.current_pdf_path is not None

            if raw.isdigit() and available and 1 <= int(raw) <= len(available):
                chosen_path = available[int(raw) - 1]
            else:
                chosen_path = Path(raw)

            try:
                self.editor.open_pdf(chosen_path)
                print(f"Opened {chosen_path}.")
                return True
            except Exception as exc:
                logger.error("Failed to open PDF %s: %s", chosen_path, exc)
                print(f"Could not open '{chosen_path}': {exc}")

    # ------------------------------------------------------------------
    # Rotation flow
    # ------------------------------------------------------------------
    def rotate_pages_flow(self) -> None:
        """Prompt the user for pages to rotate and rotate them in memory."""
        while True:
            pages = self._prompt_pages_to_rotate()

            if not pages:
                logger.info("No pages selected for rotation.")
                return

            confirm = input(
                f"Press 'c' to confirm rotating pages {pages}, or any other key to cancel: "
            ).strip().lower()

            if confirm == "c":
                try:
                    self.editor.rotate_pages(pages)
                    print(f"Pages {pages} rotated successfully (not yet saved).")
                except Exception as exc:
                    logger.error("Failed to rotate pages %s: %s", pages, exc)
                    print(f"Failed to rotate pages: {exc}")
            else:
                print("Rotation cancelled.")

            again = input(
                "Press 'c' to rotate more pages, or any other key to finish: "
            ).strip().lower()
            if again != "c":
                return

    def _prompt_pages_to_rotate(self) -> list[int] | None:
        num_pages = self.editor.page_count

        while True:
            raw_input_value = input(
                f"Enter the page numbers (1-{num_pages}) to rotate (comma-separated) "
                "or 'exit' to cancel: "
            ).strip()

            if raw_input_value.lower() == "exit":
                logger.info("Exiting page rotation.")
                return None

            if not raw_input_value:
                print("Please enter at least one page number.")
                continue

            try:
                pages = [int(page.strip()) for page in raw_input_value.split(",")]
            except ValueError:
                print("Please enter numbers separated by commas.")
                continue

            if any(page < 1 or page > num_pages for page in pages):
                print(f"Please enter valid page numbers between 1 and {num_pages}.")
                continue

            sorted_pages = sorted(set(pages))
            logger.info("Selected pages to rotate: %s", sorted_pages)
            return sorted_pages

    # ------------------------------------------------------------------
    # Other flows
    # ------------------------------------------------------------------
    def read_text_flow(self) -> None:
        """Print the extracted text of the open PDF."""
        try:
            print(self.editor.read_text())
        except RuntimeError as exc:
            print(f"Could not read PDF: {exc}")

    def extract_images_flow(self) -> None:
        """Ask for an output folder and extract embedded images into it."""
        output_folder = input("Output folder for extracted images: ").strip()
        count = self.editor.extract_images(output_folder)
        print(f"Extracted {count} image(s).")

    def export_pages_flow(self) -> None:
        """Ask for a page list and export it as a brand-new PDF file."""
        raw = input("Pages to export (comma-separated, e.g. 1,3,5): ").strip()
        pages = [int(page.strip()) for page in raw.split(",")] if raw else None

        try:
            output_path = self.editor.export_pages(pages=pages)
            print(f"New PDF created at {output_path}.")
        except ValueError as exc:
            print(f"Could not export pages: {exc}")

    def save_flow(self) -> None:
        """Persist in-memory changes back to the currently open file."""
        try:
            self.editor.save()
            print("Saved.")
        except RuntimeError as exc:
            print(f"Could not save: {exc}")

    # ------------------------------------------------------------------
    # Password protection flows
    # ------------------------------------------------------------------
    def encrypt_pdf_flow(self) -> None:
        """Ask for a password and encrypt the currently open PDF."""
        password = input("Password to encrypt the PDF with: ").strip()
        if not password:
            print("A password is required.")
            return

        raw_output = input(
            "Output path (leave blank to overwrite the current file): "
        ).strip()
        output_path = raw_output or None

        if self.editor.encrypt_pdf(password, output_path=output_path):
            print("PDF encrypted successfully.")
        else:
            print("Failed to encrypt PDF. See logs for details.")

    def decrypt_pdf_flow(self) -> None:
        """Ask for a password and decrypt the currently open PDF."""
        password = input("Password to decrypt the PDF with: ").strip()

        raw_output = input(
            "Output path (leave blank to overwrite the current file): "
        ).strip()
        output_path = raw_output or None

        if self.editor.decrypt_pdf(password, output_path=output_path):
            print("PDF decrypted successfully.")
        else:
            print("Failed to decrypt PDF. See logs for details.")

    # ------------------------------------------------------------------
    # Watermark flow
    # ------------------------------------------------------------------
    def watermark_flow(self) -> None:
        """Ask for a watermark file and apply it to selected pages."""
        watermark_path = input("Path to the watermark/overlay PDF: ").strip()

        raw_pages = input(
            "Pages to watermark (comma-separated, e.g. 1,3,5; blank for all pages): "
        ).strip()
        pages = [int(page.strip()) for page in raw_pages.split(",")] if raw_pages else list(
            range(1, self.editor.page_count + 1)
        )

        position = input(
            "Place watermark 'o'ver or 'u'nder the page content [o/u]: "
        ).strip().lower()
        over = position != "u"

        raw_output = input(
            "Output path (leave blank to overwrite the current file): "
        ).strip()
        output_path = raw_output or self.editor.current_pdf_path

        try:
            success = self.editor.watermark_and_overlay(
                pages=pages,
                output_path=output_path,
                watermark_path=watermark_path,
                over=over,
            )
        except ValueError as exc:
            print(f"Could not add watermark: {exc}")
            return

        if success:
            print(f"Watermark applied and saved to {output_path}.")
        else:
            print("Failed to add watermark. See logs for details.")
