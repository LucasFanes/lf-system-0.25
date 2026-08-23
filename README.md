# LF System

![Python](https://img.shields.io/badge/python-3.12-blue)
![Ruff](https://img.shields.io/badge/lint-Ruff-46a2f1)
![Tests](https://img.shields.io/badge/tests-pytest-0a7)

LF System is a local Python desktop utility suite for account control, purchase tracking, spreadsheet export, file backup workflows, and PDF operations. The official user entry point is the terminal menu launched from `Main.py`.

Portuguese version: [README-ptBR.md](README-ptBR.md)

## Features

- Terminal menu for local file, backup, billing, spreadsheet, and PDF workflows.
- Account and customer records backed by SQLite.
- Purchase history with NC codes.
- Excel report generation and Google Sheets import/export support.
- ZIP backup, item copy, folder copy, and recycle-bin deletion helpers.
- Integrated graphical PDF editor opened from `[D] Editor de PDF`.
- PDF page rendering, navigation, zoom modes, rotation, extraction, encryption, decryption, and watermark actions.

## Architecture

- `Main.py`: the only official command-line entry point.
- `lf_system/app.py`: top-level TUI routing and integration handlers.
- `lf_system/billing.py`: billing business rules.
- `lf_system/database.py`: SQLite persistence.
- `lf_system/file_operations.py`: local file operations and backup helpers.
- `lf_system/spreadsheet.py`: Excel and Google Sheets workflows.
- `lf_system/pdf_operationsfolder/`: PDF core, GUI state/controller, renderer, and compatibility terminal menu.
- `tests/`: pytest test suite with generated temporary fixtures only.
- `tools/`: maintenance utilities that are not part of normal startup.

## Requirements

- Python 3.12.
- Windows is the primary target. The automated quality workflow also runs tests on Linux.
- A virtual environment is recommended.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .[dev]
```

On Linux/macOS shells, activate your environment normally and run:

```bash
python -m pip install -e ".[dev]"
```

## Running

Use one official command:

```powershell
python Main.py
```

Open the PDF editor from the main menu with:

```text
[D] Editor de PDF
```

Internal modules such as `lf_system.pdf_operationsfolder.pdf_gui` are not documented as standalone applications.

## Tests and Quality

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_run
```

Current local validation: 53 tests passing, with 37.38% total coverage. Main covered areas include PDF core/controller/renderer, PDF integration, config, database persistence, file backup filtering, utility prompts, and basic app navigation.

The CI workflow is defined in `.github/workflows/quality.yml` and runs Ruff plus pytest with coverage on Windows and Linux using Python 3.12. GUI behavior is tested with mocks or non-interactive smoke checks; CI does not require manually opening windows.

## Project Structure

```text
LF-System/
  Main.py
  AGENTS.md
  CHANGELOG.md
  ROADMAP_PDF.md
  README.md
  README-ptBR.md
  pyproject.toml
  .github/workflows/quality.yml
  .vscode/settings.json
  lf_system/
    app.py
    billing.py
    config.py
    database.py
    file_operations.py
    logging_config.py
    spreadsheet.py
    utils.py
    pdf_operationsfolder/
      exceptions.py
      pdf_basic.py
      pdf_editor.py
      pdf_gui.py
      pdf_gui_controller.py
      pdf_gui_state.py
      pdf_menu.py
      pdf_renderer.py
      pdf_view_settings.py
      utils.py
  tests/
    fixtures/
    integration/
    unit/
  tools/
    inspect_billing_database.py
```

## Known Limitations

- `.pytest_cache` and `.pytest_tmp` from earlier Windows runs may remain inaccessible because of local ACLs; new cache and temp folders are ignored and disposable.
- The graphical PDF editor is integrated through the TUI, but full end-to-end GUI automation remains intentionally limited.
- Google Sheets operations depend on local EZSheets credentials and network availability.
- Billing and spreadsheet modules still have lower automated coverage than the PDF subsystem.
