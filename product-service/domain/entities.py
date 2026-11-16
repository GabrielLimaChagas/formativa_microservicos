from dataclasses import dataclass
from typing import Optional
from domain.exceptions import ValidationException

@dataclass
class Product:
    id: Optional[int]
    name: str
    price: int = 0  # Preço em centavos

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.name or not str(self.name).strip():
            raise ValidationException("O campo 'name' é obrigatório")
        if not isinstance(self.price, int) or isinstance(self.price, bool):
            raise ValidationException("O campo 'price' deve ser numérico")

    def update(self, name: Optional[str] = None, price: Optional[int] = None):
        if name is not None:
            clean_name = str(name).strip()
            if not clean_name:
                raise ValidationException("O campo 'name' não pode ser vazio")
            self.name = clean_name

        if price is not None:
            if not isinstance(price, int) or isinstance(price, bool):
                raise ValidationException("O campo 'price' deve ser numérico")
            self.price = price
