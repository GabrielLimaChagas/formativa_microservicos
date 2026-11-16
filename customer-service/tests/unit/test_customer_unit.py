import pytest
from unittest.mock import MagicMock
from domain.entities import Customer
from domain.exceptions import ValidationException, EntityNotFoundException
from application.dtos import CreateCustomerDTO, UpdateCustomerDTO, CustomerDTO
from application.use_cases import (
    ListCustomersUseCase,
    GetCustomerUseCase,
    CreateCustomerUseCase,
    UpdateCustomerUseCase,
    DeleteCustomerUseCase,
)
from application.repositories import CustomerRepository
from application.events import EventPublisher

# ==================== DOMAIN TESTS ====================

def test_customer_entity_creation_valid():
    customer = Customer(id="1", name="Maria Silva", pipelines_count=3)
    assert customer.id == "1"
    assert customer.name == "Maria Silva"
    assert customer.pipelines_count == 3

def test_customer_entity_empty_name_raises_validation_error():
    with pytest.raises(ValidationException, match="O campo 'name' é obrigatório"):
        Customer(id="1", name="", pipelines_count=2)

def test_customer_entity_whitespace_name_raises_validation_error():
    with pytest.raises(ValidationException, match="O campo 'name' é obrigatório"):
        Customer(id="1", name="   ", pipelines_count=2)

def test_customer_entity_negative_pipelines_raises_validation_error():
    with pytest.raises(ValidationException, match="O campo 'pipelinesCount' deve ser numérico e não-negativo"):
        Customer(id="1", name="Carlos", pipelines_count=-1)

def test_customer_entity_update():
    customer = Customer(id="1", name="Carlos", pipelines_count=0)
    customer.update(name="Carlos Alterado", pipelines_count=5)
    assert customer.name == "Carlos Alterado"
    assert customer.pipelines_count == 5

def test_customer_entity_update_empty_name_fails():
    customer = Customer(id="1", name="Carlos", pipelines_count=0)
    with pytest.raises(ValidationException, match="O campo 'name' não pode ser vazio"):
        customer.update(name="   ")

# ==================== USE CASES TESTS (MOCKS) ====================

def test_list_customers_use_case():
    mock_repo = MagicMock(spec=CustomerRepository)
    mock_repo.get_all.return_value = [
        Customer(id="1", name="Ana", pipelines_count=2),
        Customer(id="2", name="Beto", pipelines_count=5),
    ]

    use_case = ListCustomersUseCase(mock_repo)
    result = use_case.execute()

    assert len(result) == 2
    assert result[0] == CustomerDTO(id="1", name="Ana", pipelines_count=2)
    assert result[1] == CustomerDTO(id="2", name="Beto", pipelines_count=5)
    mock_repo.get_all.assert_called_once()

def test_get_customer_use_case_found():
    mock_repo = MagicMock(spec=CustomerRepository)
    mock_repo.get_by_id.return_value = Customer(id="42", name="Joana", pipelines_count=1)

    use_case = GetCustomerUseCase(mock_repo)
    result = use_case.execute("42")

    assert result.id == "42"
    assert result.name == "Joana"
    assert result.pipelines_count == 1
    mock_repo.get_by_id.assert_called_once_with("42")

def test_get_customer_use_case_not_found():
    mock_repo = MagicMock(spec=CustomerRepository)
    mock_repo.get_by_id.return_value = None

    use_case = GetCustomerUseCase(mock_repo)
    with pytest.raises(EntityNotFoundException, match="Cliente não encontrado"):
        use_case.execute("999")

def test_create_customer_use_case_publishes_event():
    mock_repo = MagicMock(spec=CustomerRepository)
    mock_publisher = MagicMock(spec=EventPublisher)

    mock_repo.create.return_value = Customer(id="101", name="Novo Cliente", pipelines_count=4)

    use_case = CreateCustomerUseCase(mock_repo, event_publisher=mock_publisher)
    dto = CreateCustomerDTO(name="Novo Cliente", pipelines_count=4)
    result = use_case.execute(dto)

    assert result.id == "101"
    assert result.name == "Novo Cliente"
    assert result.pipelines_count == 4
    mock_repo.create.assert_called_once()

    # Verifica publicação do evento no Azure Service Bus / EventPublisher mock
    mock_publisher.publish.assert_called_once_with(
        event_type="CustomerCreatedEvent",
        payload={
            "customerId": "101",
            "name": "Novo Cliente",
            "pipelinesCount": 4,
        }
    )

def test_update_customer_use_case():
    mock_repo = MagicMock(spec=CustomerRepository)
    existing_customer = Customer(id="10", name="Original", pipelines_count=1)
    mock_repo.get_by_id.return_value = existing_customer
    mock_repo.update.return_value = existing_customer

    use_case = UpdateCustomerUseCase(mock_repo)
    dto = UpdateCustomerDTO(name="Atualizado", pipelines_count=10)
    result = use_case.execute("10", dto)

    assert result.name == "Atualizado"
    assert result.pipelines_count == 10
    mock_repo.update.assert_called_once()

def test_delete_customer_use_case_success():
    mock_repo = MagicMock(spec=CustomerRepository)
    mock_repo.delete.return_value = True

    use_case = DeleteCustomerUseCase(mock_repo)
    use_case.execute("10")
    mock_repo.delete.assert_called_once_with("10")

def test_delete_customer_use_case_not_found():
    mock_repo = MagicMock(spec=CustomerRepository)
    mock_repo.delete.return_value = False

    use_case = DeleteCustomerUseCase(mock_repo)
    with pytest.raises(EntityNotFoundException, match="Cliente não encontrado"):
        use_case.execute("999")
