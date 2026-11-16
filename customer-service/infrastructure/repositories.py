from typing import List, Optional
from domain.entities import Customer
from application.repositories import CustomerRepository
from infrastructure.database import db
from infrastructure.models import CustomerModel

class SQLAlchemyCustomerRepository(CustomerRepository):
    def get_all(self) -> List[Customer]:
        records = CustomerModel.query.all()
        return [
            Customer(id=r.id, name=r.name, pipelines_count=r.pipelines_count)
            for r in records
        ]

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        record = db.session.get(CustomerModel, customer_id)
        if not record:
            return None
        return Customer(id=record.id, name=record.name, pipelines_count=record.pipelines_count)

    def create(self, customer: Customer) -> Customer:
        record = CustomerModel(name=customer.name, pipelines_count=customer.pipelines_count)
        db.session.add(record)
        db.session.commit()
        return Customer(id=record.id, name=record.name, pipelines_count=record.pipelines_count)

    def update(self, customer: Customer) -> Customer:
        record = db.session.get(CustomerModel, customer.id)
        if not record:
            return customer
        record.name = customer.name
        record.pipelines_count = customer.pipelines_count
        db.session.commit()
        return Customer(id=record.id, name=record.name, pipelines_count=record.pipelines_count)

    def delete(self, customer_id: int) -> bool:
        record = db.session.get(CustomerModel, customer_id)
        if not record:
            return False
        db.session.delete(record)
        db.session.commit()
        return True

    def count(self) -> int:
        return CustomerModel.query.count()
