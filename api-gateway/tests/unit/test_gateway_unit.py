import pytest
from unittest.mock import MagicMock
from application.interfaces import HttpClient, HttpResponse
from application.services import SummaryService, HealthService
from infrastructure.jwt_service import JwtTokenService

# ==================== BFF AGGREGATION TESTS ====================

def test_summary_service_aggregation():
    mock_client = MagicMock(spec=HttpClient)

    # Simula resposta do customer-service
    mock_client.get.side_effect = [
        HttpResponse(content=b'[{"id": "1"}, {"id": "2"}]', status_code=200),
        HttpResponse(content=b'[{"id": "1"}, {"id": "2"}, {"id": "3"}]', status_code=200),
    ]

    service = SummaryService(
        http_client=mock_client,
        customers_service_url="http://cust:5001",
        products_service_url="http://prod:5002"
    )

    summary = service.get_summary()

    assert summary["customersCount"] == 2
    assert summary["productsCount"] == 3
    assert mock_client.get.call_count == 2

def test_summary_service_handles_service_failure():
    mock_client = MagicMock(spec=HttpClient)
    # Customer service falha com erro 500
    mock_client.get.side_effect = [
        HttpResponse(content=b'{"error": "Internal"}', status_code=500),
        HttpResponse(content=b'[{"id": "1"}]', status_code=200),
    ]

    service = SummaryService(
        http_client=mock_client,
        customers_service_url="http://cust:5001",
        products_service_url="http://prod:5002"
    )

    summary = service.get_summary()
    assert summary["customersCount"] == 0
    assert summary["productsCount"] == 1

def test_health_service_all_up():
    mock_client = MagicMock(spec=HttpClient)
    mock_client.get.side_effect = [
        HttpResponse(content=b'{"status": "UP"}', status_code=200),
        HttpResponse(content=b'{"status": "UP"}', status_code=200),
    ]

    service = HealthService(
        http_client=mock_client,
        customers_service_url="http://cust:5001",
        products_service_url="http://prod:5002"
    )

    data, status_code = service.check_health()
    assert status_code == 200
    assert data["status"] == "UP"
    assert data["gateway"] == "UP"
    assert data["services"]["customers"] == "UP"
    assert data["services"]["products"] == "UP"

def test_health_service_degraded():
    mock_client = MagicMock(spec=HttpClient)
    mock_client.get.side_effect = [
        HttpResponse(content=b'{"status": "UP"}', status_code=200),
        Exception("Connection refused"),
    ]

    service = HealthService(
        http_client=mock_client,
        customers_service_url="http://cust:5001",
        products_service_url="http://prod:5002"
    )

    data, status_code = service.check_health()
    assert status_code == 207
    assert data["status"] == "DEGRADED"
    assert data["services"]["customers"] == "UP"
    assert data["services"]["products"] == "DOWN"

# ==================== JWT SECURITY TESTS ====================

def test_jwt_token_service_generate_and_verify():
    jwt_svc = JwtTokenService(secret_key="my-super-secret-key-32-characters-long!!")
    payload = {"sub": "admin", "role": "manager"}

    token = jwt_svc.generate_token(payload, expires_in=60)
    assert isinstance(token, str)

    decoded = jwt_svc.verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "manager"

def test_jwt_token_service_invalid_token():
    jwt_svc = JwtTokenService(secret_key="my-super-secret-key-32-characters-long!!")
    decoded = jwt_svc.verify_token("invalid.token.structure")
    assert decoded is None
