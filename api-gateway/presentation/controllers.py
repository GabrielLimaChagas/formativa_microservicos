from flask import Blueprint, request, jsonify, Response
from domain.interfaces import HttpClient, TokenService
from application.services import SummaryService, HealthService
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

    # ==================== AUTENTICAÇÃO / LOGIN (PÚBLICO) ====================
    @bp.route("/api/auth/token", methods=["POST"])
    @bp.route("/api/auth/login", methods=["POST"])
    def login():
        """
        Emitir Token JWT de Acesso
        ---
        tags:
          - Autenticação
        parameters:
          - in: body
            name: body
            schema:
              type: object
              required:
                - username
              properties:
                username:
                  type: string
                password:
                  type: string
        responses:
          200:
            description: Token gerado com sucesso
          400:
            description: Dados incompletos
        """
        data = request.get_json() or {}
        username = data.get("username", "").strip()
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
        """
        Verificar validade do Token Bearer
        ---
        tags:
          - Autenticação
        security:
          - BearerAuth: []
        responses:
          200:
            description: Token válido
          401:
            description: Token ausente ou inválido
        """
        return jsonify({"valid": True, "user": getattr(request, "user", None)}), 200

    # ==================== ROTEAMENTO PROTEGIDO: CLIENTES ====================
    @bp.route("/api/customers", methods=["GET", "POST"])
    @auth
    def proxy_customers_root():
        """
        Proxy Clientes (Listar e Criar)
        ---
        tags:
          - Clientes (Proxy)
        security:
          - BearerAuth: []
        responses:
          200:
            description: Sucesso
          401:
            description: Não autenticado
        """
        return _forward(f"{customers_url}/customers")

    @bp.route("/api/customers/<path:subpath>", methods=["GET", "PUT", "DELETE", "POST"])
    @auth
    def proxy_customers_subpath(subpath):
        """
        Proxy Clientes (Operações por ID e Billing Request)
        ---
        tags:
          - Clientes (Proxy)
        security:
          - BearerAuth: []
        responses:
          200:
            description: Sucesso
          401:
            description: Não autenticado
        """
        return _forward(f"{customers_url}/customers/{subpath}")

    # ==================== ROTEAMENTO PROTEGIDO: PRODUTOS ====================
    @bp.route("/api/products", methods=["GET", "POST"])
    @auth
    def proxy_products_root():
        """
        Proxy Produtos (Listar e Criar)
        ---
        tags:
          - Produtos (Proxy)
        security:
          - BearerAuth: []
        responses:
          200:
            description: Sucesso
          401:
            description: Não autenticado
        """
        return _forward(f"{products_url}/products")

    @bp.route("/api/products/<path:subpath>", methods=["GET", "PUT", "DELETE", "POST"])
    @auth
    def proxy_products_subpath(subpath):
        """
        Proxy Produtos (Operações por ID, Audit Logs e Process Queue)
        ---
        tags:
          - Produtos (Proxy)
        security:
          - BearerAuth: []
        responses:
          200:
            description: Sucesso
          401:
            description: Não autenticado
        """
        return _forward(f"{products_url}/products/{subpath}")

    # ==================== BFF / MONITORAMENTO ====================
    @bp.route("/api/health", methods=["GET"])
    def health_check():
        """
        Health check público agregado do Gateway e microsserviços
        ---
        tags:
          - Monitoramento
        responses:
          200:
            description: Ecossistema totalmente saudável
          207:
            description: Ecossistema em estado degradado
        """
        data, status = health_service.check_health()
        return jsonify(data), status

    @bp.route("/api/summary", methods=["GET"])
    @auth
    def bff_summary():
        """
        Endpoint BFF Agregador de Métricas Executivas
        ---
        tags:
          - BFF
        security:
          - BearerAuth: []
        responses:
          200:
            description: Resumo consolidado retornado com sucesso
          401:
            description: Não autorizado
        """
        data = summary_service.get_summary()
        return jsonify(data), 200

    return bp
