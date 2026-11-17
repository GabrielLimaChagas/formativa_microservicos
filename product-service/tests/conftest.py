import os
import sys
import pytest

service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)

from app import create_app
from infrastructure.database import db
from infrastructure.models import ProductModel, AuditLogModel
from infrastructure.repositories import SQLAlchemyProductRepository

@pytest.fixture
def app():
    # Desativa thread real do Service Bus garantindo conexão vazia
    os.environ["AZURE_SERVICEBUS_CONNECTION_STRING"] = ""
    test_app = create_app(database_uri="sqlite:///:memory:")
    test_app.config["TESTING"] = True

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def repository(app):
    with app.app_context():
        return SQLAlchemyProductRepository()
