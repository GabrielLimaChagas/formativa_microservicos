from unittest.mock import patch

def test_health_endpoint_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "UP"
    assert data["service"] == "product-service"
    assert data["dialect"] == "sqlite"
    assert data["database"]["status"] == "UP"
    assert data["database"]["error"] is None

def test_health_endpoint_degraded_when_db_fails(client):
    with patch("presentation.controllers.db.engine.connect", side_effect=Exception("Database unreachable")):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "DEGRADED"
        assert data["database"]["status"] == "DOWN"
        assert "Database unreachable" in data["database"]["error"]

def test_product_controllers_crud_flow(client):
    # 1. Listar inicialmente vazio
    res = client.get("/products")
    assert res.status_code == 200
    assert res.get_json() == []

    # 2. Criar produto (POST 201)
    new_product = {"name": "Lavadora de Alta Pressão", "price": 89900}
    res = client.post("/products", json=new_product)
    assert res.status_code == 201
    created = res.get_json()
    prod_id = created["id"]
    assert created["name"] == "Lavadora de Alta Pressão"
    assert created["price"] == 89900

    # Validação de erro ao criar produto (POST 400)
    res_bad_name = client.post("/products", json={"name": "", "price": 100})
    assert res_bad_name.status_code == 400

    res_bad_price = client.post("/products", json={"name": "Valido", "price": "invalido"})
    assert res_bad_price.status_code == 400

    # 3. Obter produto (GET /products/<id>) 200 e 404
    res_get = client.get(f"/products/{prod_id}")
    assert res_get.status_code == 200
    assert res_get.get_json()["name"] == "Lavadora de Alta Pressão"

    res_get_404 = client.get("/products/99999")
    assert res_get_404.status_code == 404

    # 4. Atualizar produto (PUT /products/<id>) 200 e 400/404
    res_put = client.put(f"/products/{prod_id}", json={"name": "Lavadora Turbo", "price": 95000})
    assert res_put.status_code == 200
    assert res_put.get_json()["name"] == "Lavadora Turbo"
    assert res_put.get_json()["price"] == 95000

    res_put_bad_name = client.put(f"/products/{prod_id}", json={"name": "   "})
    assert res_put_bad_name.status_code == 400

    res_put_bad_price = client.put(f"/products/{prod_id}", json={"price": "not-a-number"})
    assert res_put_bad_price.status_code == 400

    res_put_404 = client.put("/products/99999", json={"name": "Inexistente"})
    assert res_put_404.status_code == 404

    # 5. Deletar produto (DELETE /products/<id>) 200 e 404
    res_del = client.delete(f"/products/{prod_id}")
    assert res_del.status_code == 200

    res_del_404 = client.delete(f"/products/{prod_id}")
    assert res_del_404.status_code == 404

    # 6. Audit logs endpoint
    res_logs = client.get("/audit-logs")
    assert res_logs.status_code == 200
    assert isinstance(res_logs.get_json(), list)
