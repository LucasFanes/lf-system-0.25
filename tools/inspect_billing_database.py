import sqlite3
from pathlib import Path


database_path = Path.home() / "SISTEMA_LF" / "Data" / "billing_accounts.sqlite3"

print(f"Verificando o arquivo: {database_path}\n")

if not database_path.exists():
    print("O arquivo do banco ainda nao existe.")
    print("Abra o Main.py, entre em Billing e cadastre uma conta para cria-lo.")
    raise SystemExit

connection = sqlite3.connect(str(database_path))
connection.row_factory = sqlite3.Row

try:
    tables = connection.execute(
        "SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name"
    ).fetchall()

    print("=== TABELAS ENCONTRADAS ===")
    if not tables:
        print("Nenhuma tabela encontrada.")
    else:
        for table in tables:
            print(f"- {table['name']}")

    print("\n=== CONTAS ===")
    accounts = connection.execute(
        "SELECT name, code, created_at, billing_items FROM accounts ORDER BY name"
    ).fetchall()

    if not accounts:
        print("Nenhuma conta cadastrada.")
    else:
        for account in accounts:
            print(dict(account))

    print("\n=== COMPRAS ===")
    purchases = connection.execute(
        """
        SELECT nc, account_name, item, price, date
        FROM purchases
        ORDER BY id
        """
    ).fetchall()

    if not purchases:
        print("Nenhuma compra cadastrada.")
    else:
        for purchase in purchases:
            print(dict(purchase))

except sqlite3.OperationalError as exc:
    print(f"Erro operacional do SQLite: {exc}")
    print("Abra o Main.py e entre em Billing uma vez para o sistema criar as tabelas.")
finally:
    connection.close()
