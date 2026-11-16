import ast
import os
import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOMER_DIR = os.path.join(BACKEND_DIR, "customer-service")
PRODUCT_DIR = os.path.join(BACKEND_DIR, "product-service")
GATEWAY_DIR = os.path.join(BACKEND_DIR, "api-gateway")

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

# ==================== CLEAN ARCHITECTURE: DOMAIN ISOLATION ====================

def test_domain_layer_does_not_import_outer_layers_or_frameworks():
    """
    Regra de Dependência Clean Architecture:
    A camada 'domain/' deve ser puramente agnóstica de frameworks externos
    e não pode importar 'application', 'infrastructure', 'presentation',
    nem 'flask', 'pymongo', 'sqlalchemy' ou 'azure'.
    """
    forbidden_in_domain = {
        "application",
        "infrastructure",
        "presentation",
        "flask",
        "pymongo",
        "sqlalchemy",
        "flask_sqlalchemy",
        "azure",
        "requests",
    }

    violations = []
    for service_dir in [CUSTOMER_DIR, PRODUCT_DIR]:
        domain_dir = os.path.join(service_dir, "domain")
        for root, _, files in os.walk(domain_dir):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, BACKEND_DIR)
                    imports = get_imported_modules(full_path)
                    for mod, line in imports:
                        root_mod = mod.split(".")[0].lower()
                        if root_mod in forbidden_in_domain:
                            violations.append(
                                f"Violação de Domínio em {rel_path}:{line} -> 'domain' importando '{mod}'"
                            )

    assert not violations, "\n".join(violations)

# ==================== CLEAN ARCHITECTURE: APPLICATION LAYER ISOLATION ====================

def test_application_layer_does_not_import_infrastructure_or_presentation():
    """
    Regra de Dependência Clean Architecture:
    A camada 'application/' pode importar 'domain', mas nunca 'infrastructure' ou 'presentation'.
    """
    forbidden_in_application = {
        "infrastructure",
        "presentation",
    }

    violations = []
    for service_dir in [CUSTOMER_DIR, PRODUCT_DIR]:
        app_dir = os.path.join(service_dir, "application")
        for root, _, files in os.walk(app_dir):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, BACKEND_DIR)
                    imports = get_imported_modules(full_path)
                    for mod, line in imports:
                        root_mod = mod.split(".")[0].lower()
                        if root_mod in forbidden_in_application:
                            violations.append(
                                f"Violação de Camada em {rel_path}:{line} -> 'application' importando '{mod}'"
                            )

    assert not violations, "\n".join(violations)

# ==================== DATABASE PER SERVICE & SERVICE ISOLATION ====================

def test_customer_and_product_services_are_isolated():
    """
    Padrão Database-per-Service:
    customer-service não importa nada de product-service e vice-versa.
    """
    violations = []
    for root, _, files in os.walk(CUSTOMER_DIR):
        if "tests" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                for mod, line in get_imported_modules(full_path):
                    if "product" in mod.lower():
                        violations.append(f"Isolamento quebrado em {file}:{line} -> customer-service importando '{mod}'")

    for root, _, files in os.walk(PRODUCT_DIR):
        if "tests" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                for mod, line in get_imported_modules(full_path):
                    if "customer" in mod.lower():
                        violations.append(f"Isolamento quebrado em {file}:{line} -> product-service importando '{mod}'")

    assert not violations, "\n".join(violations)

# ==================== GATEWAY ISOLATION ====================

def test_gateway_has_no_database_drivers_or_service_internals():
    """
    O API Gateway atua estritamente como roteador e BFF.
    Não pode importar drivers de banco de dados (sqlite3, sqlalchemy, pymongo, pyodbc)
    nem classes internas dos microsserviços.
    """
    forbidden_in_gateway = {
        "sqlite3",
        "sqlalchemy",
        "flask_sqlalchemy",
        "pymongo",
        "pyodbc",
        "pymssql",
        "psycopg2",
    }

    violations = []
    for root, _, files in os.walk(GATEWAY_DIR):
        if "tests" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, GATEWAY_DIR)
                for mod, line in get_imported_modules(full_path):
                    root_mod = mod.split(".")[0].lower()
                    if root_mod in forbidden_in_gateway:
                        violations.append(f"Gateway violação em {rel_path}:{line} -> Import de banco proibido: '{mod}'")
                    if root_mod in ["customer_service", "product_service"]:
                        violations.append(f"Gateway violação em {rel_path}:{line} -> Acoplamento com microsserviço: '{mod}'")

    assert not violations, "\n".join(violations)
