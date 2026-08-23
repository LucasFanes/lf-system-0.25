"""Filesystem operations for the LF System: backup, ZIP, delete, copy."""

from __future__ import annotations

import logging
import os
import shutil
import zipfile
from pathlib import Path

import pymsgbox
import send2trash

from .utils import generate_timestamp, show_menu

BACKUP_EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
BACKUP_EXCLUDED_FILE_NAMES = {
    ".coverage",
    "coverage.xml",
}
BACKUP_EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def _should_skip_backup_path(path: Path) -> bool:
    """Return whether a generated/local path should stay out of project backups."""
    return (
        path.name in BACKUP_EXCLUDED_FILE_NAMES
        or path.suffix in BACKUP_EXCLUDED_SUFFIXES
        or any(
            part in BACKUP_EXCLUDED_DIRS
            or part.startswith(".pytest_cache")
            or part.startswith(".pytest_tmp")
            or part.startswith(".ruff_cache")
            or part.endswith(".egg-info")
            for part in path.parts
        )
    )


def delete_item(item_path: Path) -> bool:
    """Delete a file or folder, either permanently or via the recycle bin."""
    logging.info("Starting delete process for: %s", item_path)
    if not item_path.exists():
        pymsgbox.alert("The selected file or folder does not exist.", "Error")
        return False

    key = show_menu(
        "Delete Options",
        {
            "1": f"Delete permanently (no backup) -> {item_path.name}",
            "2": f"Send to the Windows Recycle Bin -> {item_path.name}",
        },
    )

    try:
        if key == "1":
            confirmation = pymsgbox.prompt(
                text=(
                    "WARNING: This action cannot be undone.\n\n"
                    f"To permanently delete:\n'{item_path.name}'\n"
                    "type DELETE below:"
                ),
                title="Critical Confirmation",
            )
            if confirmation and confirmation.strip() == "DELETE":
                if item_path.is_file():
                    item_path.unlink()
                elif item_path.is_dir():
                    shutil.rmtree(item_path)
                logging.info("Item permanently deleted: %s", item_path.name)
                pymsgbox.alert(f"'{item_path.name}' was permanently deleted.", "Success")
                return True

            pymsgbox.alert("Action canceled.", "Canceled")
            return False

        if key == "2":
            send2trash.send2trash(item_path)
            logging.info("Item sent to Recycle Bin: %s", item_path.name)
            pymsgbox.alert(f"'{item_path.name}' was sent to the Recycle Bin.", "Success")
            return True

    except Exception as exc:
        logging.error("Error deleting item %s: %s", item_path, exc, exc_info=True)
        pymsgbox.alert(f"Error while deleting: {exc}", "Error")
        return False

    return False


def copy_single_item(source: Path, destination: Path) -> bool:
    """Copy a single file or folder (recursively) to a destination folder."""
    logging.info("Simple copy: %s -> %s", source, destination)
    try:
        if source.is_dir():
            shutil.copytree(source, destination / source.name, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)
        return True
    except Exception as exc:
        logging.error("Simple copy failed: %s", exc, exc_info=True)
        pymsgbox.alert(f"Copy failed: {exc}", "Error")
        return False


def copy_folder_contents(source: Path, destination: Path) -> bool:
    """Copy every item inside a source folder into a destination folder."""
    logging.info("Smart copy: %s -> %s", source, destination)
    try:
        items = list(source.glob("*"))
        if not items:
            return False

        for item in items:
            destination_path = destination / item.name
            if item.is_file():
                shutil.copy2(item, destination_path)
            elif item.is_dir():
                shutil.copytree(item, destination_path, dirs_exist_ok=True)
        return True
    except Exception as exc:
        logging.error("Smart copy failed: %s", exc, exc_info=True)
        pymsgbox.alert(f"Smart copy failed: {exc}", "Error")
        return False


def create_zip_backup(item_path: Path, backups_folder: Path) -> bool:
    """Create a compressed ZIP backup of a file or folder."""
    zip_name = f"Backup_{item_path.stem}_{generate_timestamp()}.zip"
    final_zip_path = backups_folder / zip_name

    try:
        with zipfile.ZipFile(final_zip_path, "w") as zip_file:
            if item_path.is_file():
                zip_file.write(
                    item_path,
                    arcname=item_path.name,
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
            else:
                for root_folder, dir_names, files in os.walk(item_path):
                    dir_names[:] = [
                        dir_name
                        for dir_name in dir_names
                        if not _should_skip_backup_path(
                            (Path(root_folder) / dir_name).relative_to(item_path)
                        )
                    ]
                    for file_name in files:
                        full_path = Path(root_folder) / file_name
                        relative_path = full_path.relative_to(item_path.parent)
                        if _should_skip_backup_path(full_path.relative_to(item_path)):
                            continue
                        zip_file.write(
                            full_path,
                            arcname=relative_path,
                            compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=9,
                        )
        pymsgbox.alert(f"Backup created:\n{zip_name}", "Success")
        return True
    except Exception as exc:
        logging.error("Zip backup failed: %s", exc, exc_info=True)
        pymsgbox.alert(f"Backup failed: {exc}", "Error")
        return False
