import json
from unittest.mock import patch, MagicMock
from domain.interfaces import HttpResponse
import requests

def test_gateway_health_endpoint_healthy(client):
    mock_resp = MagicMock()
    mock_resp.content = b'{"status": "UP"}'
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/json"}

    with patch("infrastructure.http_client.requests.get", return_value=mock_resp):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.get_json()
        assert data["gateway"] == "UP"
        assert data["status"] == "UP"
        assert data["services"]["customers"] == "UP"
        assert data["services"]["products"] == "UP"

def test_gateway_health_endpoint_degraded(client):
    def fake_requests_get(url, timeout=2.0):
        if "5001" in url or "customers" in url:
            mock_resp = MagicMock()
            mock_resp.content = b'{"status": "UP"}'
            mock_resp.status_code = 200
            mock_resp.headers = {"Content-Type": "application/json"}
            return mock_resp
        raise requests.exceptions.ConnectionError("Product service down")

    with patch("infrastructure.http_client.requests.get", side_effect=fake_requests_get):
        res = client.get("/api/health")
        assert res.status_code == 207
        data = res.get_json()
        assert data["status"] == "DEGRADED"
        assert data["services"]["customers"] == "UP"
        assert data["services"]["products"] == "DOWN"

def test_gateway_routing_to_customers(client, auth_headers):
    # Simula encaminhamento GET /api/customers com autenticação Bearer
    mock_resp = MagicMock()
    mock_resp.content = b'[{"id": "1", "name": "Maria"}]'
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/json"}

    with patch("infrastructure.http_client.requests.request", return_value=mock_resp) as mock_req:
        res = client.get("/api/customers", headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json() == [{"id": "1", "name": "Maria"}]
        mock_req.assert_called_once()
        assert "customers" in mock_req.call_args[1]["url"]

    # Simula POST /api/customers
    mock_post_resp = MagicMock()
    mock_post_resp.content = b'{"id": "2", "name": "Joao"}'
    mock_post_resp.status_code = 201
    mock_post_resp.headers = {"Content-Type": "application/json"}

    with patch("infrastructure.http_client.requests.request", return_value=mock_post_resp) as mock_req:
        res = client.post("/api/customers", json={"name": "Joao"}, headers=auth_headers)
        assert res.status_code == 201
        assert res.get_json()["name"] == "Joao"

def test_gateway_routing_to_products(client, auth_headers):
    # Simula GET /api/products/1 com autenticação Bearer
    mock_resp = MagicMock()
    mock_resp.content = b'{"id": 1, "name": "Serra"}'
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/json"}

    with patch("infrastructure.http_client.requests.request", return_value=mock_resp) as mock_req:
        res = client.get("/api/products/1", headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()["name"] == "Serra"

    # Simula 404 retornado do produto
    mock_404_resp = MagicMock()
    mock_404_resp.content = b'{"error": "Produto nao encontrado"}'
    mock_404_resp.status_code = 404
    mock_404_resp.headers = {"Content-Type": "application/json"}

    with patch("infrastructure.http_client.requests.request", return_value=mock_404_resp):
        res = client.get("/api/products/999", headers=auth_headers)
        assert res.status_code == 404
        assert res.get_json()["error"] == "Produto nao encontrado"

def test_gateway_routing_resilience_connection_error_and_timeout(client, auth_headers):
    # Simula ConnectionError -> 503 Service Unavailable
    with patch("infrastructure.http_client.requests.request", side_effect=requests.exceptions.ConnectionError("Down")):
        res = client.get("/api/customers", headers=auth_headers)
        assert res.status_code == 503
        data = res.get_json()
        assert "Falha na comunicação com o microsserviço" in data["error"]

    # Simula Timeout -> 504 Gateway Timeout
    with patch("infrastructure.http_client.requests.request", side_effect=requests.exceptions.Timeout("Timeout")):
        res = client.get("/api/products", headers=auth_headers)
        assert res.status_code == 504
        data = res.get_json()
        assert "Gateway Timeout" in data["error"]
