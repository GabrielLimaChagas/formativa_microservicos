from abc import ABC, abstractmethod
from typing import List, Optional, Union
from domain.entities import Customer

class CustomerRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Customer]:
        pass

    @abstractmethod
    def get_by_id(self, customer_id: Union[str, int]) -> Optional[Customer]:
        pass

    @abstractmethod
    def create(self, customer: Customer) -> Customer:
        pass

    @abstractmethod
    def update(self, customer: Customer) -> Customer:
        pass

    @abstractmethod
    def delete(self, customer_id: Union[str, int]) -> bool:
        pass

    @abstractmethod
    def count(self) -> int:
        pass

class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event_type: str, payload: dict) -> None:
        pass
