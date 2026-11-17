import os
import logging
from typing import List, Optional, Union, Tuple
from domain.entities import Customer
from domain.repositories import CustomerRepository

logger = logging.getLogger(__name__)

class MongoCustomerRepository(CustomerRepository):
    """
    Repositório de persistência para MongoDB (Atlas / Cosmos DB for MongoDB / Local)
    com suporte transparente a fallback em memória caso MONGODB_URI não esteja configurada.
    """
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or os.getenv("MONGODB_URI") or os.getenv("MONGODB_CONNECTION_STRING", "")
        self.db_name = db_name or os.getenv("MONGODB_DB_NAME") or os.getenv("MONGODB_DATABASE", "customers_db")
        self._client = None
        self._collection = None
        self._in_memory_store = {}
        self._next_id = 1
        self._init_connection()

    def _init_connection(self):
        if not self.uri:
            logger.info("[MongoCustomerRepository] MONGODB_URI não informada. Ativando fallback em memória.")
            return

        try:
            from pymongo import MongoClient
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Testa a conexão no boot
            self._client.admin.command("ping")
            database = self._client[self.db_name]
            self._collection = database["customers"]
            logger.info(f"[MongoCustomerRepository] Conectado ao MongoDB com sucesso (banco: {self.db_name}).")
        except Exception as e:
            logger.warning(f"[MongoCustomerRepository] Falha ao conectar ao MongoDB ({e}). Usando fallback em memória.")
            self._collection = None

    def check_health(self) -> Tuple[bool, str]:
        """
        Verifica o estado da conexão com o MongoDB executando ping.
        Retorna (is_healthy, message/error).
        """
        if not self.uri:
            return True, "in-memory-fallback"

        if not self._client:
            return False, "MongoClient não inicializado"

        try:
            self._client.admin.command("ping")
            return True, "pong"
        except Exception as e:
            return False, str(e)

    def is_configured(self) -> bool:
        return bool(self.uri and self._collection is not None)

    def _to_customer(self, doc: dict) -> Customer:
        # Garante que _id (ObjectId ou string) é serializado como str
        doc_id = str(doc.get("_id") or doc.get("id"))
        return Customer(
            id=doc_id,
            name=doc["name"],
            pipelines_count=doc.get("pipelines_count", 0)
        )

    def get_all(self) -> List[Customer]:
        if self._collection is not None:
            try:
                docs = list(self._collection.find())
                return [self._to_customer(d) for d in docs]
            except Exception as e:
                logger.error(f"Erro ao listar clientes no MongoDB: {e}")

        return [
            Customer(id=str(c["id"]), name=c["name"], pipelines_count=c["pipelines_count"])
            for c in self._in_memory_store.values()
        ]

    def get_by_id(self, customer_id: Union[str, int]) -> Optional[Customer]:
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
                    return self._to_customer(doc)
            except Exception as e:
                logger.error(f"Erro ao buscar cliente por ID no MongoDB: {e}")

        # Fallback em memória
        c = self._in_memory_store.get(str_id)
        if not c:
            return None
        return Customer(id=str(c["id"]), name=c["name"], pipelines_count=c["pipelines_count"])

    def create(self, customer: Customer) -> Customer:
        if self._collection is not None:
            try:
                doc = {
                    "name": customer.name,
                    "pipelines_count": customer.pipelines_count
                }
                result = self._collection.insert_one(doc)
                str_id = str(result.inserted_id)
                return Customer(id=str_id, name=customer.name, pipelines_count=customer.pipelines_count)
            except Exception as e:
                logger.error(f"Erro ao criar cliente no MongoDB: {e}")
                raise

        # Fallback em memória
        new_id = str(self._next_id)
        self._next_id += 1
        self._in_memory_store[new_id] = {
            "id": new_id,
            "name": customer.name,
            "pipelines_count": customer.pipelines_count
        }
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
                logger.error(f"Erro ao atualizar cliente no MongoDB: {e}")
                raise

        # Fallback em memória
        if str_id in self._in_memory_store:
            self._in_memory_store[str_id]["name"] = customer.name
            self._in_memory_store[str_id]["pipelines_count"] = customer.pipelines_count
        return customer

    def delete(self, customer_id: Union[str, int]) -> bool:
        str_id = str(customer_id)
        if self._collection is not None:
            try:
                from bson import ObjectId
                query = {"_id": ObjectId(str_id)} if ObjectId.is_valid(str_id) else {"_id": str_id}
                res = self._collection.delete_one(query)
                return res.deleted_count > 0
            except Exception as e:
                logger.error(f"Erro ao deletar cliente no MongoDB: {e}")
                raise

        # Fallback em memória
        if str_id in self._in_memory_store:
            del self._in_memory_store[str_id]
            return True
        return False

    def count(self) -> int:
        if self._collection is not None:
            try:
                return self._collection.count_documents({})
            except Exception as e:
                logger.error(f"Erro ao contar documentos no MongoDB: {e}")

        return len(self._in_memory_store)

    def seed_initial_data(self) -> None:
        """Seed idempotente: insere Maria e Antônio apenas se o banco/coleção estiver vazio."""
        if self.count() == 0:
            self.create(Customer(id=None, name="Maria", pipelines_count=2))
            self.create(Customer(id=None, name="Antônio", pipelines_count=27))
            logger.info("[MongoCustomerRepository] Seed de dados iniciais para Clientes aplicado com sucesso.")
