import os
import logging
from typing import List, Optional
from domain.entities import Customer
from application.repositories import CustomerRepository

logger = logging.getLogger(__name__)

class MongoDBCustomerRepository(CustomerRepository):
    """
    Repositório concreto para MongoDB e Azure Cosmos DB (API MongoDB).
    Se o MongoDB não estiver acessível ou a connection string não estiver ativa localmente,
    possui fallback transparente em memória para permitir testes unitários/locais sem quebras.
    """
    def __init__(self, connection_string: Optional[str] = None, database_name: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("MONGODB_CONNECTION_STRING", "")
        self.database_name = database_name or os.getenv("MONGODB_DATABASE", "customers_db")
        self._collection = None
        self._fallback_store = {}
        self._next_fallback_id = 1
        self._init_mongo()

    def _init_mongo(self):
        if not self.connection_string:
            logger.info("MONGODB_CONNECTION_STRING não configurada. Usando fallback em memória no repositório.")
            return

        try:
            from pymongo import MongoClient
            client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
            # Testa conexão
            client.admin.command("ping")
            db = client[self.database_name]
            self._collection = db["customers"]
            logger.info(f"Conexão bem sucedida com MongoDB/Cosmos DB no banco '{self.database_name}'.")
        except Exception as e:
            logger.warning(f"Não foi possível conectar ao MongoDB ({e}). Ativando fallback em memória.")
            self._collection = None

    def get_all(self) -> List[Customer]:
        if self._collection is not None:
            try:
                docs = list(self._collection.find())
                return [
                    Customer(
                        id=str(d.get("_id") or d.get("id")),
                        name=d["name"],
                        pipelines_count=d.get("pipelines_count", 0)
                    )
                    for d in docs
                ]
            except Exception as e:
                logger.error(f"Erro ao consultar MongoDB: {e}")

        return [
            Customer(id=str(c["id"]), name=c["name"], pipelines_count=c["pipelines_count"])
            for c in self._fallback_store.values()
        ]

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        str_id = str(customer_id)
        if self._collection is not None:
            try:
                from bson import ObjectId
                doc = None
                if ObjectId.is_valid(str_id):
                    doc = self._collection.find_one({"_id": ObjectId(str_id)})
                if not doc:
                    doc = self._collection.find_one({"_id": str_id}) or self._collection.find_one({"id": str_id})

                if doc:
                    return Customer(
                        id=str(doc.get("_id") or doc.get("id")),
                        name=doc["name"],
                        pipelines_count=doc.get("pipelines_count", 0)
                    )
            except Exception as e:
                logger.error(f"Erro ao buscar por ID no MongoDB: {e}")

        # Fallback
        c = self._fallback_store.get(str_id)
        if not c:
            return None
        return Customer(id=str(c["id"]), name=c["name"], pipelines_count=c["pipelines_count"])

    def create(self, customer: Customer) -> Customer:
        if self._collection is not None:
            try:
                from bson import ObjectId
                doc = {
                    "name": customer.name,
                    "pipelines_count": customer.pipelines_count
                }
                result = self._collection.insert_one(doc)
                str_id = str(result.inserted_id)
                return Customer(id=str_id, name=customer.name, pipelines_count=customer.pipelines_count)
            except Exception as e:
                logger.error(f"Erro ao inserir no MongoDB: {e}")

        # Fallback
        new_id = str(self._next_fallback_id)
        self._next_fallback_id += 1
        doc = {
            "id": new_id,
            "name": customer.name,
            "pipelines_count": customer.pipelines_count
        }
        self._fallback_store[new_id] = doc
        return Customer(id=new_id, name=customer.name, pipelines_count=customer.pipelines_count)

    def update(self, customer: Customer) -> Customer:
        str_id = str(customer.id)
        if self._collection is not None:
            try:
                from bson import ObjectId
                query = {"_id": ObjectId(str_id)} if ObjectId.is_valid(str_id) else {"_id": str_id}
                update_fields = {
                    "name": customer.name,
                    "pipelines_count": customer.pipelines_count
                }
                self._collection.update_one(query, {"$set": update_fields})
                return customer
            except Exception as e:
                logger.error(f"Erro ao atualizar no MongoDB: {e}")

        # Fallback
        if str_id in self._fallback_store:
            self._fallback_store[str_id]["name"] = customer.name
            self._fallback_store[str_id]["pipelines_count"] = customer.pipelines_count
        return customer

    def delete(self, customer_id: str) -> bool:
        str_id = str(customer_id)
        if self._collection is not None:
            try:
                from bson import ObjectId
                query = {"_id": ObjectId(str_id)} if ObjectId.is_valid(str_id) else {"_id": str_id}
                res = self._collection.delete_one(query)
                if res.deleted_count > 0:
                    return True
            except Exception as e:
                logger.error(f"Erro ao deletar no MongoDB: {e}")

        # Fallback
        if str_id in self._fallback_store:
            del self._fallback_store[str_id]
            return True
        return False

    def count(self) -> int:
        if self._collection is not None:
            try:
                return self._collection.count_documents({})
            except Exception as e:
                logger.error(f"Erro count no MongoDB: {e}")

        return len(self._fallback_store)

    def seed_initial_data(self):
        if self.count() == 0:
            self.create(Customer(id=None, name="Maria", pipelines_count=2))
            self.create(Customer(id=None, name="Antônio", pipelines_count=27))
            logger.info("Seed de dados para Clientes aplicado com sucesso!")
