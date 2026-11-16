import pytest
from unittest.mock import MagicMock
from domain.entities import Product
from domain.exceptions import ValidationException, EntityNotFoundException
from application.dtos import CreateProductDTO, UpdateProductDTO, ProductDTO
from application.use_cases import (
    ListProductsUseCase,
    GetProductUseCase,
    CreateProductUseCase,
    UpdateProductUseCase,
    DeleteProductUseCase,
)
from application.repositories import ProductRepository
from application.events import AuditService

# ==================== DOMAIN TESTS ====================

def test_product_entity_creation_valid():
    product = Product(id=1, name="Furadeira", price=19990)
    assert product.id == 1
    assert product.name == "Furadeira"
    assert product.price == 19990

def test_product_entity_empty_name_raises_validation_error():
    with pytest.raises(ValidationException, match="O campo 'name' é obrigatório"):
        Product(id=1, name="", price=1000)

def test_product_entity_invalid_price_raises_validation_error():
    with pytest.raises(ValidationException, match="O campo 'price' deve ser numérico"):
        Product(id=1, name="Prego", price="abc") # type: ignore

def test_product_entity_update():
    product = Product(id=1, name="Original", price=1000)
    product.update(name="Novo Nome", price=2500)
    assert product.name == "Novo Nome"
    assert product.price == 2500

def test_product_entity_update_empty_name_fails():
    product = Product(id=1, name="Original", price=1000)
    with pytest.raises(ValidationException, match="O campo 'name' não pode ser vazio"):
        product.update(name="   ")

# ==================== USE CASES TESTS (MOCKS) ====================

def test_list_products_use_case():
    mock_repo = MagicMock(spec=ProductRepository)
    mock_repo.get_all.return_value = [
        Product(id=1, name="Item A", price=5000),
        Product(id=2, name="Item B", price=12000),
    ]

    use_case = ListProductsUseCase(mock_repo)
    result = use_case.execute()

    assert len(result) == 2
    assert result[0] == ProductDTO(id="1", name="Item A", price=5000)
    assert result[1] == ProductDTO(id="2", name="Item B", price=12000)
    mock_repo.get_all.assert_called_once()

def test_get_product_use_case_found():
    mock_repo = MagicMock(spec=ProductRepository)
    mock_repo.get_by_id.return_value = Product(id=5, name="Serra Elétrica", price=35000)

    use_case = GetProductUseCase(mock_repo)
    result = use_case.execute(5)

    assert result.id == "5"
    assert result.name == "Serra Elétrica"
    assert result.price == 35000
    mock_repo.get_by_id.assert_called_once_with(5)

def test_get_product_use_case_not_found():
    mock_repo = MagicMock(spec=ProductRepository)
    mock_repo.get_by_id.return_value = None

    use_case = GetProductUseCase(mock_repo)
    with pytest.raises(EntityNotFoundException, match="Produto não encontrado"):
        use_case.execute(999)

def test_create_product_use_case():
    mock_repo = MagicMock(spec=ProductRepository)
    mock_repo.create.return_value = Product(id=10, name="Novo Produto", price=4500)

    use_case = CreateProductUseCase(mock_repo)
    dto = CreateProductDTO(name="Novo Produto", price=4500)
    result = use_case.execute(dto)

    assert result.id == "10"
    assert result.name == "Novo Produto"
    assert result.price == 4500
    mock_repo.create.assert_called_once()

def test_update_product_use_case():
    mock_repo = MagicMock(spec=ProductRepository)
    prod = Product(id=2, name="Antigo", price=1000)
    mock_repo.get_by_id.return_value = prod
    mock_repo.update.return_value = prod

    use_case = UpdateProductUseCase(mock_repo)
    dto = UpdateProductDTO(name="Novo", price=2000)
    result = use_case.execute(2, dto)

    assert result.name == "Novo"
    assert result.price == 2000
    mock_repo.update.assert_called_once()

def test_delete_product_use_case():
    mock_repo = MagicMock(spec=ProductRepository)
    mock_repo.delete.return_value = True

    use_case = DeleteProductUseCase(mock_repo)
    use_case.execute(2)
    mock_repo.delete.assert_called_once_with(2)

def test_audit_service_log_event():
    mock_session = MagicMock()
    mock_model = MagicMock()
    instance = MagicMock()
    instance.id = 1
    instance.to_dict.return_value = {"id": "1", "eventType": "CustomerCreatedEvent", "payload": "{}", "createdAt": None}
    mock_model.return_value = instance

    audit = AuditService(mock_session, mock_model)
    res = audit.log_event("CustomerCreatedEvent", {"customerId": "1"})

    assert res["id"] == "1"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
