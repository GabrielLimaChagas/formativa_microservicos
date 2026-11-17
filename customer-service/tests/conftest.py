import os
import sys
import pytest

service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)

from app import create_app
from infrastructure.mongo_repository import MongoCustomerRepository
from infrastructure.event_publisher import clear_in_memory_event_bus

@pytest.fixture
def repository():
    # Repositório isolado em memória (URI vazia ativa o fallback em memória)
    return MongoCustomerRepository(uri="", db_name="test_customers_db")

@pytest.fixture
def app(repository):
    clear_in_memory_event_bus()
    test_app = create_app(repo=repository)
    test_app.config["TESTING"] = True
    return test_app

@pytest.fixture
def client(app):
    return app.test_client()
