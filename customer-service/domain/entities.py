from dataclasses import dataclass
from typing import Optional, Union
from domain.exceptions import ValidationException

@dataclass
class Customer:
    id: Optional[Union[str, int]]
    name: str
    pipelines_count: int = 0

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.name or not str(self.name).strip():
            raise ValidationException("O campo 'name' é obrigatório")
        try:
            int_pipes = int(self.pipelines_count)
            if int_pipes < 0 or isinstance(self.pipelines_count, bool):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValidationException("O campo 'pipelinesCount' deve ser numérico e não-negativo")

    def update(self, name: Optional[str] = None, pipelines_count: Optional[int] = None):
        if name is not None:
            clean_name = str(name).strip()
            if not clean_name:
                raise ValidationException("O campo 'name' não pode ser vazio")
            self.name = clean_name

        if pipelines_count is not None:
            try:
                int_pipes = int(pipelines_count)
                if int_pipes < 0 or isinstance(pipelines_count, bool):
                    raise ValueError()
                self.pipelines_count = int_pipes
            except (ValueError, TypeError):
                raise ValidationException("O campo 'pipelinesCount' deve ser numérico e não-negativo")
