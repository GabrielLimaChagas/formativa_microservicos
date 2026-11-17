import os
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from infrastructure.http_client import RequestsHttpClient
from infrastructure.jwt_service import JwtTokenService
from application.services import SummaryService, HealthService
from presentation.controllers import create_gateway_blueprint

def create_app():
    app = Flask(__name__)

    # Configuração de CORS produtivo via CORS_ALLOWED_ORIGINS
    cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "*").strip()
    if cors_origins_env == "*":
        allowed_origins = "*"
    else:
        allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]

    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    # Swagger / OpenAPI
    app.config['SWAGGER'] = {
        'title': 'API Gateway & BFF',
        'uiversion': 3,
        'specs_route': '/api/docs/',
        'securityDefinitions': {
            'BearerAuth': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'Token JWT no formato: Bearer <token>'
            }
        }
    }
    Swagger(app)

    customers_service_url = os.getenv("CUSTOMERS_SERVICE_URL", "http://localhost:5001")
    products_service_url = os.getenv("PRODUCTS_SERVICE_URL", "http://localhost:5002")

    jwt_secret = os.getenv("JWT_SECRET_KEY", "secret-cloud-native-key-2026-super-secure-32bytes")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    # Injeção de dependências (Composition Root)
    http_client = RequestsHttpClient()
    token_service = JwtTokenService(secret_key=jwt_secret, algorithm=jwt_algorithm)
    summary_service = SummaryService(http_client, customers_service_url, products_service_url)
    health_service = HealthService(http_client, customers_service_url, products_service_url)

    gateway_bp = create_gateway_blueprint(
        http_client=http_client,
        summary_service=summary_service,
        health_service=health_service,
        token_service=token_service,
        customers_service_url=customers_service_url,
        products_service_url=products_service_url,
    )
    app.register_blueprint(gateway_bp)
    app.token_service = token_service

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"API Gateway / BFF iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
