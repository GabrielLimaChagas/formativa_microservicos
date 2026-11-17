import json
from unittest.mock import patch, MagicMock
from infrastructure.event_publisher import get_in_memory_event_bus

def test_health_endpoint_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "customer-service"
    assert data["database"] == "mongodb"
    assert "mongoConfigured" in data

def test_health_endpoint_degraded_when_db_fails(app, client):
    # Simula falha na checagem de saúde do banco MongoDB
    with patch.object(app.customer_repo, "check_health", return_value=(False, "Connection timeout to cluster")):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "DEGRADED"
        assert data["database"] == "mongodb"
        assert "error" in data

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

    # 4. Obter cliente por ID (GET 200)
    res_get = client.get(f"/customers/{cust_id}")
    assert res_get.status_code == 200
    assert res_get.get_json()["name"] == "Cliente Teste"

    # 5. Obter cliente inexistente (GET 404)
    res_404 = client.get("/customers/999999")
    assert res_404.status_code == 404

    # 6. Atualizar cliente (PUT 200)
    update_payload = {"name": "Cliente Teste Atualizado", "pipelinesCount": 8}
    res_put = client.put(f"/customers/{cust_id}", json=update_payload)
    assert res_put.status_code == 200
    assert res_put.get_json()["name"] == "Cliente Teste Atualizado"
    assert res_put.get_json()["pipelinesCount"] == 8

    # 7. Solicitação de faturamento assíncrono (POST 202)
    res_bill = client.post(f"/customers/{cust_id}/billing-request", json={"amountCents": 5000})
    assert res_bill.status_code == 202
    assert res_bill.get_json()["status"] == "QUEUED"

    # 8. Remover cliente (DELETE 200)
    res_del = client.delete(f"/customers/{cust_id}")
    assert res_del.status_code == 200

    # 9. Verificar que foi removido
    res_after = client.get(f"/customers/{cust_id}")
    assert res_after.status_code == 404
