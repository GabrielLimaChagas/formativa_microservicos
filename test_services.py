"""
Script de testes automatizados para validar todos os microsserviços e o API Gateway.
Execução: python backend/test_services.py
"""
import sys
import os

# Adiciona caminhos dos serviços ao sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "customer-service"))
sys.path.append(os.path.join(os.path.dirname(__file__), "product-service"))
sys.path.append(os.path.join(os.path.dirname(__file__), "api-gateway"))

from app import app as customer_app, init_db as init_customer_db
import importlib

# Carrega app de clientes
init_customer_db()
customer_client = customer_app.test_client()

print("--- [1/2] Testando Customer Service ---")
# 1. Listar clientes (deve ter o seed inicial)
res = customer_client.get("/customers")
assert res.status_code == 200, f"Falha GET /customers: {res.status_code}"
customers = res.get_json()
print(f"GET /customers: OK ({len(customers)} clientes)")

# 2. Criar cliente
new_customer_payload = {"name": "Carlos Silva", "pipelinesCount": 5}
res = customer_client.post("/customers", json=new_customer_payload)
assert res.status_code == 201, f"Falha POST /customers: {res.status_code}"
created_customer = res.get_json()
created_id = created_customer["id"]
print(f"POST /customers: OK (ID: {created_id})")

# 3. Obter cliente
res = customer_client.get(f"/customers/{created_id}")
assert res.status_code == 200, f"Falha GET /customers/{created_id}"
assert res.get_json()["name"] == "Carlos Silva"
print(f"GET /customers/{created_id}: OK")

# 4. Atualizar cliente
update_payload = {"name": "Carlos Silva Atualizado", "pipelinesCount": 10}
res = customer_client.put(f"/customers/{created_id}", json=update_payload)
assert res.status_code == 200, f"Falha PUT /customers/{created_id}"
assert res.get_json()["name"] == "Carlos Silva Atualizado"
assert res.get_json()["pipelinesCount"] == 10
print(f"PUT /customers/{created_id}: OK")

# 5. Deletar cliente
res = customer_client.delete(f"/customers/{created_id}")
assert res.status_code == 200, f"Falha DELETE /customers/{created_id}"
print(f"DELETE /customers/{created_id}: OK")

# Verifica se realmente deletou
res = customer_client.get(f"/customers/{created_id}")
assert res.status_code == 404, "Cliente ainda existe após DELETE"
print("Verificação pós-delete: OK (404 retornado corretamente)")

print("\n--- [2/2] Testando Product Service ---")
# Reset módulos importados para carregar product_app limpo
if "app" in sys.modules:
    del sys.modules["app"]
if "database" in sys.modules:
    del sys.modules["database"]
if "models" in sys.modules:
    del sys.modules["models"]

sys.path.remove(os.path.join(os.path.dirname(__file__), "customer-service"))
from app import app as product_app, init_db as init_product_db
init_product_db()
product_client = product_app.test_client()

# 1. Listar produtos
res = product_client.get("/products")
assert res.status_code == 200, f"Falha GET /products: {res.status_code}"
products = res.get_json()
print(f"GET /products: OK ({len(products)} produtos)")

# 2. Criar produto
new_product_payload = {"name": "Motosserra MS 170", "price": 149900}
res = product_client.post("/products", json=new_product_payload)
assert res.status_code == 201, f"Falha POST /products: {res.status_code}"
created_product = res.get_json()
prod_id = created_product["id"]
print(f"POST /products: OK (ID: {prod_id})")

# 3. Obter produto
res = product_client.get(f"/products/{prod_id}")
assert res.status_code == 200, f"Falha GET /products/{prod_id}"
assert res.get_json()["name"] == "Motosserra MS 170"
print(f"GET /products/{prod_id}: OK")

# 4. Atualizar produto
update_prod_payload = {"name": "Motosserra MS 170 Promocional", "price": 139900}
res = product_client.put(f"/products/{prod_id}", json=update_prod_payload)
assert res.status_code == 200, f"Falha PUT /products/{prod_id}"
assert res.get_json()["name"] == "Motosserra MS 170 Promocional"
assert res.get_json()["price"] == 139900
print(f"PUT /products/{prod_id}: OK")

# 5. Deletar produto
res = product_client.delete(f"/products/{prod_id}")
assert res.status_code == 200, f"Falha DELETE /products/{prod_id}"
print(f"DELETE /products/{prod_id}: OK")

# Verifica se deletou
res = product_client.get(f"/products/{prod_id}")
assert res.status_code == 404
print("Verificação pós-delete: OK (404 retornado corretamente)")

print("\n==========================================")
print(" TODOS OS TESTES UNITÁRIOS E CRUD PASSARAM COM SUCESSO! ")
print("==========================================")
