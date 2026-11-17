import logging
from typing import List, Optional
from domain.entities import Customer
from application.repositories import CustomerRepository
from infrastructure.database import db
from infrastructure.models import CustomerModel

logger = logging.getLogger(__name__)

class SQLAlchemyCustomerRepository(CustomerRepository):
    """
    Repositório concreto para SQL Server / Azure SQL Database e SQLite (local).
    Converte os identificadores numéricos do banco para string conforme o contrato de domínio.
    """

    def get_all(self) -> List[Customer]:
        records = CustomerModel.query.all()
        return [
            Customer(
                id=str(r.id),
                name=r.name,
                pipelines_count=r.pipelines_count
            )
            for r in records
        ]

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        try:
            int_id = int(customer_id)
        except (ValueError, TypeError):
            return None

        record = db.session.get(CustomerModel, int_id)
        if not record:
            return None
        return Customer(
            id=str(record.id),
            name=record.name,
            pipelines_count=record.pipelines_count
        )

    def create(self, customer: Customer) -> Customer:
        record = CustomerModel(
            name=customer.name,
            pipelines_count=customer.pipelines_count
        )
        try:
            db.session.add(record)
            db.session.commit()
            return Customer(
                id=str(record.id),
                name=record.name,
                pipelines_count=record.pipelines_count
            )
        except Exception:
            db.session.rollback()
            raise

    def update(self, customer: Customer) -> Customer:
        try:
            int_id = int(customer.id)
        except (ValueError, TypeError):
            return customer

        record = db.session.get(CustomerModel, int_id)
        if not record:
            return customer

        try:
            record.name = customer.name
            record.pipelines_count = customer.pipelines_count
            db.session.commit()
            return Customer(
                id=str(record.id),
                name=record.name,
                pipelines_count=record.pipelines_count
            )
        except Exception:
            db.session.rollback()
            raise

    def delete(self, customer_id: str) -> bool:
        try:
            int_id = int(customer_id)
        except (ValueError, TypeError):
            return False

        record = db.session.get(CustomerModel, int_id)
        if not record:
            return False

        try:
            db.session.delete(record)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise

    def count(self) -> int:
        return CustomerModel.query.count()

    def seed_initial_data(self) -> None:
        if self.count() == 0:
            seed_data = [
                CustomerModel(name="Maria", pipelines_count=2),
                CustomerModel(name="Antônio", pipelines_count=27),
            ]
            try:
                db.session.bulk_save_objects(seed_data)
                db.session.commit()
                logger.info("Seed de dados para Clientes aplicado com sucesso!")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erro ao aplicar seed inicial de Clientes: {e}")
                raise
