from flask import Blueprint, request, jsonify, Response
from application.interfaces import HttpClient
from application.services import SummaryService, HealthService
from application.security import TokenService
from presentation.auth_middleware import require_auth

def create_gateway_blueprint(
    http_client: HttpClient,
    summary_service: SummaryService,
    health_service: HealthService,
    token_service: TokenService,
    customers_service_url: str,
    products_service_url: str,
) -> Blueprint:
    bp = Blueprint("gateway", __name__)
    customers_url = customers_service_url.rstrip("/")
    products_url = products_service_url.rstrip("/")
    auth = require_auth(token_service)

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

    # ==================== AUTENTICAÇÃO / LOGIN ====================
    @bp.route("/api/auth/login", methods=["POST"])
    def login():
        """
        Endpoint centralizado de login/geração de token JWT.
        Em ambiente padrão aceita credenciais de teste para emissão de Bearer Token.
        """
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        # Validação simples para emissão do token
        if not username:
            return jsonify({"error": "Campo 'username' obrigatório"}), 400

        token = token_service.generate_token({"sub": username, "role": "admin"})
        return jsonify({
            "token": token,
            "tokenType": "Bearer",
            "expiresIn": 3600,
            "user": username
        }), 200

    @bp.route("/api/auth/verify", methods=["GET"])
    @auth
    def verify():
        return jsonify({"valid": True, "user": getattr(request, "user", None)}), 200

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
