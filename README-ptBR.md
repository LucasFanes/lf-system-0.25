# LF System

![Python](https://img.shields.io/badge/python-3.12-blue)
![Ruff](https://img.shields.io/badge/lint-Ruff-46a2f1)
![Testes](https://img.shields.io/badge/testes-pytest-0a7)

LF System e um conjunto local de utilitarios desktop em Python para controle de contas, historico de compras, exportacao de planilhas, backups de arquivos e operacoes em PDF. O ponto oficial de entrada para o usuario e o menu de terminal iniciado por `Main.py`.

Versao em ingles: [README.md](README.md)

## Funcionalidades

- Menu de terminal para arquivos, backups, cobranca, planilhas e PDF.
- Cadastro de contas e clientes com persistencia SQLite.
- Historico de compras com codigos NC.
- Geracao de relatorios Excel e suporte a importacao/exportacao via Google Sheets.
- Backup ZIP, copia de itens, copia de pastas e exclusao pela lixeira.
- Editor grafico de PDF integrado pela opcao `[D] Editor de PDF`.
- Visualizacao de paginas, navegacao, modos de zoom, rotacao, extracao, criptografia, descriptografia e marca-d'agua em PDFs.

## Arquitetura

- `Main.py`: unico ponto oficial de entrada.
- `lf_system/app.py`: roteamento do menu principal e integracoes.
- `lf_system/billing.py`: regras de negocio de cobranca.
- `lf_system/database.py`: persistencia SQLite.
- `lf_system/file_operations.py`: operacoes locais de arquivos e backups.
- `lf_system/spreadsheet.py`: fluxos Excel e Google Sheets.
- `lf_system/pdf_operationsfolder/`: nucleo PDF, estado/controlador da GUI, renderizacao e menu terminal de compatibilidade.
- `tests/`: suite pytest com fixtures temporarias geradas pelos testes.
- `tools/`: utilitarios de manutencao fora da inicializacao normal.

## Requisitos

- Python 3.12.
- Windows e o alvo principal. O workflow automatico tambem executa testes no Linux.
- Uso de ambiente virtual recomendado.

## Instalacao

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .[dev]
```

Em shells Linux/macOS, ative o ambiente e execute:

```bash
python -m pip install -e ".[dev]"
```

## Execucao

Use um unico comando oficial:

```powershell
python Main.py
```

Abra o editor de PDF pelo menu principal com:

```text
[D] Editor de PDF
```

Modulos internos, como `lf_system.pdf_operationsfolder.pdf_gui`, nao sao documentados como programas principais.

## Testes e Qualidade

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_run
```

Validacao local atual: 53 testes passando, com 37,38% de cobertura total. As areas cobertas incluem nucleo/controlador/renderizador de PDF, integracao do PDF, config, persistencia do banco, filtro de backup, prompts utilitarios e navegacao basica do app.

O CI esta em `.github/workflows/quality.yml` e executa Ruff mais pytest com cobertura no Windows e Linux usando Python 3.12. Comportamentos graficos usam mocks ou verificacoes nao interativas; o CI nao exige abertura manual de janelas.

## Estrutura Final

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

## Limitacoes Conhecidas

- `.pytest_cache` e `.pytest_tmp` de execucoes antigas no Windows podem continuar inacessiveis por ACL local; novas pastas de cache e temporarios sao ignoradas e descartaveis.
- O editor grafico de PDF esta integrado ao TUI, mas a automacao end-to-end de GUI permanece limitada de proposito.
- Operacoes do Google Sheets dependem de credenciais EZSheets locais e disponibilidade de rede.
- Os modulos de cobranca e planilhas ainda possuem cobertura automatizada menor que o subsistema de PDF.
