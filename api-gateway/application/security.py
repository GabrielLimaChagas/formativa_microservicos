import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class TokenService(ABC):
    @abstractmethod
    def generate_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        pass
