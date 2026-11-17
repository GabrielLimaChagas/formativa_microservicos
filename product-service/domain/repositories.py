from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import Product

class ProductRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Product]:
        pass

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]:
        pass

    @abstractmethod
    def create(self, product: Product) -> Product:
        pass

    @abstractmethod
    def update(self, product: Product) -> Product:
        pass

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        pass

    @abstractmethod
    def count(self) -> int:
        pass

class EventConsumer(ABC):
    @abstractmethod
    def start_listening(self) -> None:
        pass

    @abstractmethod
    def process_event(self, event_type: str, payload: dict) -> None:
        pass
