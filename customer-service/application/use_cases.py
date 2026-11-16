from typing import List, Optional
from domain.entities import Customer
from domain.exceptions import EntityNotFoundException
from application.repositories import CustomerRepository
from application.dtos import CustomerDTO, CreateCustomerDTO, UpdateCustomerDTO
from application.events import EventPublisher

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

    def execute(self, customer_id: str) -> CustomerDTO:
        customer = self._repository.get_by_id(str(customer_id))
        if not customer:
            raise EntityNotFoundException("Cliente não encontrado")
        return CustomerDTO(id=str(customer.id), name=customer.name, pipelines_count=customer.pipelines_count)

class CreateCustomerUseCase:
    def __init__(self, repository: CustomerRepository, event_publisher: Optional[EventPublisher] = None):
        self._repository = repository
        self._event_publisher = event_publisher

    def execute(self, dto: CreateCustomerDTO) -> CustomerDTO:
        customer = Customer(
            id=None,
            name=dto.name,
            pipelines_count=dto.pipelines_count
        )
        created = self._repository.create(customer)
        result = CustomerDTO(id=str(created.id), name=created.name, pipelines_count=created.pipelines_count)

        if self._event_publisher:
            self._event_publisher.publish(
                event_type="CustomerCreatedEvent",
                payload={
                    "customerId": result.id,
                    "name": result.name,
                    "pipelinesCount": result.pipelines_count,
                }
            )

        return result

class UpdateCustomerUseCase:
    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, customer_id: str, dto: UpdateCustomerDTO) -> CustomerDTO:
        customer = self._repository.get_by_id(str(customer_id))
        if not customer:
            raise EntityNotFoundException("Cliente não encontrado")

        customer.update(name=dto.name, pipelines_count=dto.pipelines_count)
        updated = self._repository.update(customer)
        return CustomerDTO(id=str(updated.id), name=updated.name, pipelines_count=updated.pipelines_count)

class DeleteCustomerUseCase:
    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, customer_id: str) -> None:
        deleted = self._repository.delete(str(customer_id))
        if not deleted:
            raise EntityNotFoundException("Cliente não encontrado")
