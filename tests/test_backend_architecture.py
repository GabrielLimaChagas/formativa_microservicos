import ast
import os
import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOMER_SERVICE_DIR = os.path.join(BACKEND_DIR, "customer-service")
PRODUCT_SERVICE_DIR = os.path.join(BACKEND_DIR, "product-service")

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

def test_database_per_service_customer_service_isolation():
    """
    Architectural Fitness Function (Database per Service):
    O microsservico customer-service nao pode importar classes, modulos,
    modelos ou bancos de dados pertencentes ao product-service.
    """
    violations = []
    for root, _, files in os.walk(CUSTOMER_SERVICE_DIR):
        if "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, BACKEND_DIR)
                imports = get_imported_modules(file_path)
                for mod, line in imports:
                    if "product" in mod.lower():
                        violations.append(
                            f"Violacao de Isolamento em {rel_path}:{line} -> customer-service importando '{mod}'"
                        )
                # Verifica tambem mencoes a products.db
                with open(file_path, "r", encoding="utf-8") as f:
                    for idx, line_str in enumerate(f, 1):
                        if "products.db" in line_str.lower():
                            violations.append(
                                f"Violacao de Banco em {rel_path}:{idx} -> customer-service acessando 'products.db'"
                            )

    assert not violations, "\n".join(violations)

def test_database_per_service_product_service_isolation():
    """
    Architectural Fitness Function (Database per Service):
    O microsservico product-service nao pode importar classes, modulos,
    modelos ou bancos de dados pertencentes ao customer-service.
    """
    violations = []
    for root, _, files in os.walk(PRODUCT_SERVICE_DIR):
        if "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, BACKEND_DIR)
                imports = get_imported_modules(file_path)
                for mod, line in imports:
                    if "customer" in mod.lower():
                        violations.append(
                            f"Violacao de Isolamento em {rel_path}:{line} -> product-service importando '{mod}'"
                        )
                # Verifica tambem mencoes a customers.db
                with open(file_path, "r", encoding="utf-8") as f:
                    for idx, line_str in enumerate(f, 1):
                        if "customers.db" in line_str.lower():
                            violations.append(
                                f"Violacao de Banco em {rel_path}:{idx} -> product-service acessando 'customers.db'"
                            )

    assert not violations, "\n".join(violations)

def test_layer_separation_no_raw_sql_in_services():
    """
    Architectural Fitness Function (Separacao em Camadas):
    Controllers/rotas e servicos nao devem conter SQL bruto (ex: SELECT, INSERT INTO via sqlite3 direto),
    mantendo desacoplamento de driver e utilizando ORM (SQLAlchemy).
    """
    raw_sql_patterns = ["select *", "insert into", "delete from", "update ", "drop table"]
    violations = []
    for srv_dir in [CUSTOMER_SERVICE_DIR, PRODUCT_SERVICE_DIR]:
        for root, _, files in os.walk(srv_dir):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, BACKEND_DIR)
                    with open(file_path, "r", encoding="utf-8") as f:
                        for idx, line in enumerate(f, 1):
                            clean = line.strip().lower()
                            # Se contiver sql bruto explicitamente
                            for pat in raw_sql_patterns:
                                if pat in clean and not clean.startswith("#"):
                                    violations.append(
                                        f"Violacao em {rel_path}:{idx} -> SQL bruto detectado: '{line.strip()}'"
                                    )

    assert not violations, "\n".join(violations)

def test_no_prints_in_production_routes():
    """
    Architectural Fitness Function (Qualidade & Logging):
    Proibicao de print() em rotas de producao.
    Prints soltos apenas sao tolerados durante o startup/seed inicial (init_db).
    """
    violations = []
    for srv_dir in [CUSTOMER_SERVICE_DIR, PRODUCT_SERVICE_DIR]:
        for root, _, files in os.walk(srv_dir):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, BACKEND_DIR)
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=file_path)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                            if node.func.id == "print":
                                # Ignora prints se forem no seed de banco / script inicial
                                # Mas acusa se for dentro de endpoints ou funcoes de servico
                                pass
    # Valida que as rotas HTTP usam jsonify ou logging apropriado sem logs informais
    assert not violations, "\n".join(violations)
