from dataclasses import dataclass
from typing import Optional
from domain.exceptions import ValidationException

@dataclass
class Customer:
    id: Optional[int]
    name: str
    pipelines_count: int = 0

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.name or not str(self.name).strip():
            raise ValidationException("O campo 'name' é obrigatório")
        if not isinstance(self.pipelines_count, int) or self.pipelines_count < 0:
            raise ValidationException("O campo 'pipelinesCount' deve ser numérico e não-negativo")

    def update(self, name: Optional[str] = None, pipelines_count: Optional[int] = None):
        if name is not None:
            clean_name = str(name).strip()
            if not clean_name:
                raise ValidationException("O campo 'name' não pode ser vazio")
            self.name = clean_name

        if pipelines_count is not None:
            if not isinstance(pipelines_count, int) or isinstance(pipelines_count, bool):
                raise ValidationException("O campo 'pipelinesCount' deve ser numérico")
            if pipelines_count < 0:
                raise ValidationException("O campo 'pipelinesCount' deve ser numérico e não-negativo")
            self.pipelines_count = pipelines_count
