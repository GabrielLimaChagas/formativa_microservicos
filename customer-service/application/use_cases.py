from typing import List, Optional, Union
from domain.entities import Customer
from domain.exceptions import EntityNotFoundException
from domain.repositories import CustomerRepository, EventPublisher
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

    def execute(self, customer_id: Union[str, int]) -> CustomerDTO:
        customer = self._repository.get_by_id(customer_id)
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

    def execute(self, customer_id: Union[str, int], dto: UpdateCustomerDTO) -> CustomerDTO:
        customer = self._repository.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundException("Cliente não encontrado")

        customer.update(name=dto.name, pipelines_count=dto.pipelines_count)
        updated = self._repository.update(customer)
        return CustomerDTO(id=str(updated.id), name=updated.name, pipelines_count=updated.pipelines_count)

class DeleteCustomerUseCase:
    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, customer_id: Union[str, int]) -> None:
        deleted = self._repository.delete(customer_id)
        if not deleted:
            raise EntityNotFoundException("Cliente não encontrado")

class BillingRequestUseCase:
    """
    Solicitação de faturamento/processamento assíncrono para o cliente.
    Dispara evento no Azure Service Bus com dados para faturamento.
    """
    def __init__(self, repository: CustomerRepository, event_publisher: Optional[EventPublisher] = None):
        self._repository = repository
        self._event_publisher = event_publisher

    def execute(self, customer_id: Union[str, int], amount_cents: int = 0, description: str = "") -> dict:
        customer = self._repository.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundException("Cliente não encontrado")

        payload = {
            "customerId": str(customer.id),
            "customerName": customer.name,
            "pipelinesCount": customer.pipelines_count,
            "amountCents": amount_cents,
            "description": description or "Faturamento solicitado",
        }

        if self._event_publisher:
            self._event_publisher.publish(
                event_type="BillingRequestedEvent",
                payload=payload
            )

        return {
            "status": "QUEUED",
            "message": f"Solicitação de faturamento para o cliente {customer.name} (ID: {customer.id}) enviada com sucesso.",
            "event": "BillingRequestedEvent",
            "payload": payload
        }
