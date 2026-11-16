from flask import Blueprint, request, jsonify, Response
from application.interfaces import HttpClient
from application.services import SummaryService, HealthService

def create_gateway_blueprint(
    http_client: HttpClient,
    summary_service: SummaryService,
    health_service: HealthService,
    customers_service_url: str,
    products_service_url: str,
) -> Blueprint:
    bp = Blueprint("gateway", __name__)
    customers_url = customers_service_url.rstrip("/")
    products_url = products_service_url.rstrip("/")

    def _forward(target_url: str):
        headers = {key: value for key, value in request.headers if key.lower() not in ["host", "content-length"]}
        response = http_client.forward(
            method=request.method,
            target_url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            timeout=5.0
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.content_type
        )

    # ==================== ROTEAMENTO: CLIENTES ====================
    @bp.route("/api/customers", methods=["GET", "POST"])
    def proxy_customers_root():
        return _forward(f"{customers_url}/customers")

    @bp.route("/api/customers/<path:subpath>", methods=["GET", "PUT", "DELETE"])
    def proxy_customers_subpath(subpath):
        return _forward(f"{customers_url}/customers/{subpath}")

    # ==================== ROTEAMENTO: PRODUTOS ====================
    @bp.route("/api/products", methods=["GET", "POST"])
    def proxy_products_root():
        return _forward(f"{products_url}/products")

    @bp.route("/api/products/<path:subpath>", methods=["GET", "PUT", "DELETE"])
    def proxy_products_subpath(subpath):
        return _forward(f"{products_url}/products/{subpath}")

    # ==================== BFF / MONITORAMENTO ====================
    @bp.route("/api/health", methods=["GET"])
    def health_check():
        data, status = health_service.check_health()
        return jsonify(data), status

    @bp.route("/api/summary", methods=["GET"])
    def bff_summary():
        data = summary_service.get_summary()
        return jsonify(data), 200

    return bp
