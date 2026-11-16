from typing import List
from domain.entities import Customer
from domain.exceptions import EntityNotFoundException, ValidationException
from application.repositories import CustomerRepository
from application.dtos import CustomerDTO, CreateCustomerDTO, UpdateCustomerDTO

class ListCustomersUseCase:
    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self) -> List[CustomerDTO]:
        customers = self._repository.get_all()
        return [
            CustomerDTO(id=str(c.id), name=c.name, pipelines_count=c.pipelines_count)
            for c in customers
        ]

class GetCustomerUseCase:
    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, customer_id: int) -> CustomerDTO:
        customer = self._repository.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundException("Cliente não encontrado")
        return CustomerDTO(id=str(customer.id), name=customer.name, pipelines_count=customer.pipelines_count)

class CreateCustomerUseCase:
    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, dto: CreateCustomerDTO) -> CustomerDTO:
        customer = Customer(
            id=None,
            name=dto.name,
            pipelines_count=dto.pipelines_count
        )
        created = self._repository.create(customer)
        return CustomerDTO(id=str(created.id), name=created.name, pipelines_count=created.pipelines_count)

class UpdateCustomerUseCase:
    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, customer_id: int, dto: UpdateCustomerDTO) -> CustomerDTO:
        customer = self._repository.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundException("Cliente não encontrado")

        customer.update(name=dto.name, pipelines_count=dto.pipelines_count)
        updated = self._repository.update(customer)
        return CustomerDTO(id=str(updated.id), name=updated.name, pipelines_count=updated.pipelines_count)

class DeleteCustomerUseCase:
    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, customer_id: int) -> None:
        deleted = self._repository.delete(customer_id)
        if not deleted:
            raise EntityNotFoundException("Cliente não encontrado")
