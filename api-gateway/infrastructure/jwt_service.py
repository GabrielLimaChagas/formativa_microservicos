import time
import jwt
from typing import Dict, Any, Optional
from application.security import TokenService

class JwtTokenService(TokenService):
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def generate_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        data = dict(payload)
        now = int(time.time())
        data["iat"] = now
        data["exp"] = now + expires_in
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            decoded = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return decoded
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
