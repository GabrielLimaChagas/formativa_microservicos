from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class HttpResponse:
    def __init__(self, content: bytes, status_code: int, headers: Optional[Dict[str, str]] = None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "application/json")

class HttpClient(ABC):
    @abstractmethod
    def forward(
        self,
        method: str,
        target_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: bytes,
        timeout: float = 5.0
    ) -> HttpResponse:
        pass

    @abstractmethod
    def get(self, url: str, timeout: float = 2.0) -> HttpResponse:
        pass

class TokenService(ABC):
    @abstractmethod
    def generate_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        pass
