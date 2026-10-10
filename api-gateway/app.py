import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
# Habilita CORS para todas as origens ou origens dos microfrontends
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configurações de URLs dos Microsserviços
CUSTOMERS_SERVICE_URL = os.getenv("CUSTOMERS_SERVICE_URL", "http://localhost:5001")
PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL", "http://localhost:5002")

def forward_request(target_url):
    """
    Função utilitária de Gateway/Reverse Proxy que encaminha a requisição 
    ao microsserviço de destino preservando método, headers, params e body.
    """
    method = request.method
    headers = {key: value for key, value in request.headers if key.lower() not in ["host", "content-length"]}
    params = request.args
    data = request.get_data()

    try:
        resp = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            params=params,
            data=data,
            timeout=5.0
        )
        # Retorna resposta preservando código de status e content-type
        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get("content-type", "application/json")
        )
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Falha na comunicação com o microsserviço",
            "target": target_url,
            "status": "Service Unavailable"
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Tempo de requisição ao microsserviço expirou (Gateway Timeout)",
            "target": target_url
        }), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ROTEAMENTO: CLIENTES ====================

@app.route("/api/customers", methods=["GET", "POST"])
def proxy_customers_root():
    target = f"{CUSTOMERS_SERVICE_URL}/customers"
    return forward_request(target)

@app.route("/api/customers/<path:subpath>", methods=["GET", "PUT", "DELETE"])
def proxy_customers_subpath(subpath):
    target = f"{CUSTOMERS_SERVICE_URL}/customers/{subpath}"
    return forward_request(target)

# ==================== ROTEAMENTO: PRODUTOS ====================

@app.route("/api/products", methods=["GET", "POST"])
def proxy_products_root():
    target = f"{PRODUCTS_SERVICE_URL}/products"
    return forward_request(target)

@app.route("/api/products/<path:subpath>", methods=["GET", "PUT", "DELETE"])
def proxy_products_subpath(subpath):
    target = f"{PRODUCTS_SERVICE_URL}/products/{subpath}"
    return forward_request(target)

# ==================== BFF / MONITORAMENTO ====================

@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Health check agregado do API Gateway e dos microsserviços dependentes.
    """
    services_status = {}

    # Check Customer Service
    try:
        c_res = requests.get(f"{CUSTOMERS_SERVICE_URL}/health", timeout=2.0)
        services_status["customers"] = "UP" if c_res.status_code == 200 else f"ERROR ({c_res.status_code})"
    except Exception:
        services_status["customers"] = "DOWN"

    # Check Product Service
    try:
        p_res = requests.get(f"{PRODUCTS_SERVICE_URL}/health", timeout=2.0)
        services_status["products"] = "UP" if p_res.status_code == 200 else f"ERROR ({p_res.status_code})"
    except Exception:
        services_status["products"] = "DOWN"

    overall_status = "UP" if all(v == "UP" for v in services_status.values()) else "DEGRADED"

    return jsonify({
        "gateway": "UP",
        "status": overall_status,
        "services": services_status
    }), (200 if overall_status == "UP" else 207)

@app.route("/api/summary", methods=["GET"])
def bff_summary():
    """
    Endpoint BFF de composição de dados: consolida métricas para o dashboard
    reduzindo o número de round-trips do frontend (padrão BFF).
    """
    summary = {
        "customersCount": 0,
        "productsCount": 0
    }
    try:
        c_res = requests.get(f"{CUSTOMERS_SERVICE_URL}/customers", timeout=3.0)
        if c_res.status_code == 200:
            summary["customersCount"] = len(c_res.json())
    except Exception:
        pass

    try:
        p_res = requests.get(f"{PRODUCTS_SERVICE_URL}/products", timeout=3.0)
        if p_res.status_code == 200:
            summary["productsCount"] = len(p_res.json())
    except Exception:
        pass

    return jsonify(summary), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"API Gateway / BFF iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
