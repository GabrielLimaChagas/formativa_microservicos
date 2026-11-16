from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CustomerDTO:
    id: str
    name: str
    pipelines_count: int

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "pipelinesCount": self.pipelines_count
        }

@dataclass(frozen=True)
class CreateCustomerDTO:
    name: str
    pipelines_count: int = 0

@dataclass(frozen=True)
class UpdateCustomerDTO:
    name: Optional[str] = None
    pipelines_count: Optional[int] = None
