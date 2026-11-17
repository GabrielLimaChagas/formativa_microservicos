import pytest
from unittest.mock import MagicMock
from domain.entities import Customer
from infrastructure.mongo_repository import MongoCustomerRepository

def test_mongo_repository_crud(repository):
    # 1. Inicia vazio
    assert repository.count() == 0
    assert repository.get_all() == []

    # 2. Create
    new_customer = Customer(id=None, name="Empresa XPTO", pipelines_count=3)
    created = repository.create(new_customer)
    assert created.id is not None
    assert created.name == "Empresa XPTO"
    assert created.pipelines_count == 3
    assert repository.count() == 1

    # 3. Get by ID
    found = repository.get_by_id(created.id)
    assert found is not None
    assert str(found.id) == str(created.id)
    assert found.name == "Empresa XPTO"
    assert found.pipelines_count == 3

    # 4. Get by non-existing ID / invalid ID
    assert repository.get_by_id("99999") is None
    assert repository.get_by_id("invalid-id") is None

    # 5. Update
    found.update(name="Empresa XPTO Atualizada", pipelines_count=10)
    updated = repository.update(found)
    assert updated.name == "Empresa XPTO Atualizada"
    assert updated.pipelines_count == 10

    refetched = repository.get_by_id(created.id)
    assert refetched.name == "Empresa XPTO Atualizada"
    assert refetched.pipelines_count == 10

    # 6. Delete
    deleted = repository.delete(created.id)
    assert deleted is True
    assert repository.count() == 0
    assert repository.get_by_id(created.id) is None

    # Delete em ID inexistente
    assert repository.delete("99999") is False

def test_mongo_repository_seed_idempotent(repository):
    assert repository.count() == 0
    repository.seed_initial_data()
    assert repository.count() == 2

    # Executar novamente não duplica dados
    repository.seed_initial_data()
    assert repository.count() == 2

    names = [c.name for c in repository.get_all()]
    assert "Maria" in names
    assert "Antônio" in names

def test_mongo_health_check_in_memory_and_mock():
    # Fallback em memória
    repo = MongoCustomerRepository(uri="", db_name="test_db")
    healthy, msg = repo.check_health()
    assert healthy is True
    assert msg == "in-memory-fallback"
    assert repo.is_configured() is False

    # Mock de MongoClient ping com sucesso
    mock_client = MagicMock()
    mock_client.admin.command.return_value = {"ok": 1}
    repo._client = mock_client
    repo.uri = "mongodb://localhost:27017/test_db"
    healthy, msg = repo.check_health()
    assert healthy is True
    assert msg == "pong"

    # Mock de MongoClient ping com falha
    mock_client.admin.command.side_effect = Exception("Connection timeout")
    healthy, msg = repo.check_health()
    assert healthy is False
    assert "Connection timeout" in msg

def test_health_endpoint_200_and_503(app, repository, client):
    # 1. Health 200 (UP / HEALTHY)
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "customer-service"
    assert data["database"] == "mongodb"
    assert data["mongoConfigured"] is False

    # 2. Simular falha de conexão com MongoDB (retornando 503 DEGRADED)
    repository.check_health = MagicMock(return_value=(False, "Failed to connect to cluster: Authentication failed"))
    res_err = client.get("/health")
    assert res_err.status_code == 503
    err_data = res_err.get_json()
    assert err_data["status"] == "DEGRADED"
    assert err_data["database"] == "mongodb"
    assert "error" in err_data
