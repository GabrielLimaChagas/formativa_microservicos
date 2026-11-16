from abc import ABC, abstractmethod
from typing import Dict, Any

class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        pass
