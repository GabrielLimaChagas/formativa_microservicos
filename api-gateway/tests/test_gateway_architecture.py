import ast
import os
import pytest

GATEWAY_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DISALLOWED_DATABASE_MODULES = {
    "sqlite3",
    "sqlalchemy",
    "flask_sqlalchemy",
    "psycopg2",
    "pymysql",
    "mysql",
    "tortoise",
    "peewee",
    "databases",
}

def get_imported_modules(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno))
    return imports

def test_gateway_has_no_database_or_persistence_imports():
    """
    Architectural Fitness Function:
    O API Gateway atua estritamente como roteador/proxy reverso.
    Nenhum arquivo do gateway pode importar drivers de banco de dados ou ORMs.
    """
    python_files = []
    for root, _, files in os.walk(GATEWAY_DIR):
        if "tests" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    assert python_files, f"Nenhum arquivo Python encontrado em {GATEWAY_DIR}"

    violations = []
    for py_file in python_files:
        rel_path = os.path.relpath(py_file, GATEWAY_DIR)
        imports = get_imported_modules(py_file)
        for mod, line in imports:
            root_mod = mod.split(".")[0].lower()
            if root_mod in DISALLOWED_DATABASE_MODULES:
                violations.append(
                    f"Violacao em {rel_path}:{line} -> Import de banco de dados proibido: '{mod}'"
                )

    assert not violations, "\n".join(violations)

def test_gateway_does_not_import_backend_domain_services():
    """
    Architectural Fitness Function:
    O Gateway nao pode importar modulos internos de customer-service ou product-service.
    Toda integracao com o backend deve ser feita via HTTP/Network (proxy).
    """
    python_files = []
    for root, _, files in os.walk(GATEWAY_DIR):
        if "tests" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    violations = []
    for py_file in python_files:
        rel_path = os.path.relpath(py_file, GATEWAY_DIR)
        imports = get_imported_modules(py_file)
        for mod, line in imports:
            root_mod = mod.split(".")[0].lower()
            if root_mod in ["customer_service", "product_service", "models", "database"]:
                violations.append(
                    f"Violacao em {rel_path}:{line} -> Acoplamento indevido com dominio backend: '{mod}'"
                )

    assert not violations, "\n".join(violations)

def test_gateway_routes_act_as_proxy_and_do_not_contain_sql():
    """
    Architectural Fitness Function:
    Rotas do gateway nao devem conter strings ou comandos SQL.
    """
    python_files = []
    for root, _, files in os.walk(GATEWAY_DIR):
        if "tests" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    sql_keywords = ["select *", "insert into", "delete from", "update set", "create table"]
    violations = []
    for py_file in python_files:
        rel_path = os.path.relpath(py_file, GATEWAY_DIR)
        with open(py_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                clean_line = line.lower()
                for keyword in sql_keywords:
                    if keyword in clean_line:
                        violations.append(
                            f"Violacao em {rel_path}:{idx} -> Comando SQL bruto detectado no Gateway: '{line.strip()}'"
                        )

    assert not violations, "\n".join(violations)
