import json
from unittest.mock import patch
from infrastructure.event_publisher import get_in_memory_event_bus

def test_health_endpoint_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "UP"
    assert data["service"] == "customer-service"
    assert data["dialect"] == "sqlite"
    assert data["database"]["status"] == "UP"
    assert data["database"]["error"] is None

def test_health_endpoint_degraded_when_db_fails(client):
    # Simula falha na conexão/execução do banco
    with patch("presentation.controllers.db.engine.connect", side_effect=Exception("Database connection timeout")):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "DEGRADED"
        assert data["database"]["status"] == "DOWN"
        assert "Database connection timeout" in data["database"]["error"]

def test_customer_controllers_crud_flow(client):
    # 1. Listar inicialmente vazio
    res = client.get("/customers")
    assert res.status_code == 200
    assert res.get_json() == []

    # 2. Criar cliente com sucesso (POST) - funciona mesmo sem Azure Service Bus configurado
    create_payload = {"name": "Cliente Teste", "pipelinesCount": 4}
    res = client.post("/customers", json=create_payload)
    assert res.status_code == 201
    created = res.get_json()
    cust_id = created["id"]
    assert created["name"] == "Cliente Teste"
    assert created["pipelinesCount"] == 4

    # Verifica publicação do evento no fallback in-memory seguro
    bus = get_in_memory_event_bus()
    assert len(bus) >= 1
    assert bus[-1]["eventType"] == "CustomerCreatedEvent"
    assert bus[-1]["payload"]["customerId"] == cust_id

    # 3. Validação de erro ao criar cliente (POST 400)
    res_bad_name = client.post("/customers", json={"name": "   ", "pipelinesCount": 1})
    assert res_bad_name.status_code == 400
    assert "name" in res_bad_name.get_json()["error"]

    res_empty_body = client.post("/customers", json={})
    assert res_empty_body.status_code == 400

    # 4. Obter cliente (GET /customers/<id>) 200 e 404
    res_get = client.get(f"/customers/{cust_id}")
    assert res_get.status_code == 200
    assert res_get.get_json()["name"] == "Cliente Teste"

    res_get_404 = client.get("/customers/99999")
    assert res_get_404.status_code == 404

    # 5. Atualizar cliente (PUT /customers/<id>)
    update_payload = {"name": "Cliente Teste Atualizado", "pipelinesCount": 8}
    res_put = client.put(f"/customers/{cust_id}", json=update_payload)
    assert res_put.status_code == 200
    assert res_put.get_json()["name"] == "Cliente Teste Atualizado"
    assert res_put.get_json()["pipelinesCount"] == 8

    # PUT validações de erro
    res_put_empty_name = client.put(f"/customers/{cust_id}", json={"name": ""})
    assert res_put_empty_name.status_code == 400

    res_put_bad_pipelines = client.put(f"/customers/{cust_id}", json={"pipelinesCount": "invalid"})
    assert res_put_bad_pipelines.status_code == 400

    res_put_404 = client.put("/customers/99999", json={"name": "Nao Existe"})
    assert res_put_404.status_code == 404

    # 6. Deletar cliente (DELETE /customers/<id>) 200 e 404
    res_del = client.delete(f"/customers/{cust_id}")
    assert res_del.status_code == 200

    # Segunda deleção retorna 404
    res_del_404 = client.delete(f"/customers/{cust_id}")
    assert res_del_404.status_code == 404
