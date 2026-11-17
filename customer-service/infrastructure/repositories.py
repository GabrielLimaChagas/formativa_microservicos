from typing import List, Optional, Union
from domain.entities import Customer
from domain.repositories import CustomerRepository
from infrastructure.database import db
from infrastructure.models import CustomerModel

class SQLAlchemyCustomerRepository(CustomerRepository):
    def get_all(self) -> List[Customer]:
        records = CustomerModel.query.all()
        return [
            Customer(id=str(r.id), name=r.name, pipelines_count=r.pipelines_count)
            for r in records
        ]

    def get_by_id(self, customer_id: Union[str, int]) -> Optional[Customer]:
        try:
            c_id = int(customer_id)
        except (ValueError, TypeError):
            return None
        record = db.session.get(CustomerModel, c_id)
        if not record:
            return None
        return Customer(id=str(record.id), name=record.name, pipelines_count=record.pipelines_count)

    def create(self, customer: Customer) -> Customer:
        record = CustomerModel(name=customer.name, pipelines_count=customer.pipelines_count)
        db.session.add(record)
        db.session.commit()
        return Customer(id=str(record.id), name=record.name, pipelines_count=record.pipelines_count)

    def update(self, customer: Customer) -> Customer:
        try:
            c_id = int(customer.id)
        except (ValueError, TypeError):
            return customer

        record = db.session.get(CustomerModel, c_id)
        if not record:
            return customer
        record.name = customer.name
        record.pipelines_count = customer.pipelines_count
        db.session.commit()
        return Customer(id=str(record.id), name=record.name, pipelines_count=record.pipelines_count)

    def delete(self, customer_id: Union[str, int]) -> bool:
        try:
            c_id = int(customer_id)
        except (ValueError, TypeError):
            return False
        record = db.session.get(CustomerModel, c_id)
        if not record:
            return False
        db.session.delete(record)
        db.session.commit()
        return True

    def count(self) -> int:
        return CustomerModel.query.count()

    def seed_initial_data(self) -> None:
        if self.count() == 0:
            seed_data = [
                CustomerModel(name="Maria", pipelines_count=2),
                CustomerModel(name="Antônio", pipelines_count=27),
            ]
            db.session.bulk_save_objects(seed_data)
            db.session.commit()
