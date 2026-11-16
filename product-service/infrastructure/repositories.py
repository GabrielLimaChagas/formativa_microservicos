from typing import List, Optional
from domain.entities import Product
from application.repositories import ProductRepository
from infrastructure.database import db
from infrastructure.models import ProductModel

class SQLAlchemyProductRepository(ProductRepository):
    def get_all(self) -> List[Product]:
        records = ProductModel.query.all()
        return [
            Product(id=r.id, name=r.name, price=r.price)
            for r in records
        ]

    def get_by_id(self, product_id: int) -> Optional[Product]:
        record = db.session.get(ProductModel, product_id)
        if not record:
            return None
        return Product(id=record.id, name=record.name, price=record.price)

    def create(self, product: Product) -> Product:
        record = ProductModel(name=product.name, price=product.price)
        db.session.add(record)
        db.session.commit()
        return Product(id=record.id, name=record.name, price=record.price)

    def update(self, product: Product) -> Product:
        record = db.session.get(ProductModel, product.id)
        if not record:
            return product
        record.name = product.name
        record.price = product.price
        db.session.commit()
        return Product(id=record.id, name=record.name, price=record.price)

    def delete(self, product_id: int) -> bool:
        record = db.session.get(ProductModel, product_id)
        if not record:
            return False
        db.session.delete(record)
        db.session.commit()
        return True

    def count(self) -> int:
        return ProductModel.query.count()
