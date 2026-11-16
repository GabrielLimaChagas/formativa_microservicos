from typing import List
from domain.entities import Product
from domain.exceptions import EntityNotFoundException, ValidationException
from application.repositories import ProductRepository
from application.dtos import ProductDTO, CreateProductDTO, UpdateProductDTO

class ListProductsUseCase:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    def execute(self) -> List[ProductDTO]:
        products = self._repository.get_all()
        return [
            ProductDTO(id=str(p.id), name=p.name, price=p.price)
            for p in products
        ]

class GetProductUseCase:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    def execute(self, product_id: int) -> ProductDTO:
        product = self._repository.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Produto não encontrado")
        return ProductDTO(id=str(product.id), name=product.name, price=product.price)

class CreateProductUseCase:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    def execute(self, dto: CreateProductDTO) -> ProductDTO:
        product = Product(
            id=None,
            name=dto.name,
            price=dto.price
        )
        created = self._repository.create(product)
        return ProductDTO(id=str(created.id), name=created.name, price=created.price)

class UpdateProductUseCase:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    def execute(self, product_id: int, dto: UpdateProductDTO) -> ProductDTO:
        product = self._repository.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Produto não encontrado")

        product.update(name=dto.name, price=dto.price)
        updated = self._repository.update(product)
        return ProductDTO(id=str(updated.id), name=updated.name, price=updated.price)

class DeleteProductUseCase:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    def execute(self, product_id: int) -> None:
        deleted = self._repository.delete(product_id)
        if not deleted:
            raise EntityNotFoundException("Produto não encontrado")
