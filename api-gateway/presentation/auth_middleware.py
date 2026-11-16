from functools import wraps
from flask import request, jsonify
from application.security import TokenService

def require_auth(token_service: TokenService):
    """
    Middleware decorator para proteção de rotas centralizada no Gateway.
    Valida cabeçalho 'Authorization: Bearer <token>' usando TokenService.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({"error": "Cabeçalho 'Authorization' ausente", "status": "Unauthorized"}), 401

            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify({"error": "Formato do token inválido. Esperado: 'Bearer <token>'", "status": "Unauthorized"}), 401

            token = parts[1]
            payload = token_service.verify_token(token)
            if not payload:
                return jsonify({"error": "Token JWT inválido ou expirado", "status": "Unauthorized"}), 401

            # Armazena dados do usuário autenticado no request context
            request.user = payload
            return f(*args, **kwargs)
        return decorated
    return decorator
