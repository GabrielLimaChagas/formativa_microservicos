from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ProductDTO:
    id: str
    name: str
    price: int

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price
        }

@dataclass(frozen=True)
class CreateProductDTO:
    name: str
    price: int = 0

@dataclass(frozen=True)
class UpdateProductDTO:
    name: Optional[str] = None
    price: Optional[int] = None
