import os
import sys
import pytest

service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)

from app import create_app

@pytest.fixture
def app():
    test_app = create_app()
    test_app.config["TESTING"] = True
    return test_app

@pytest.fixture
def client(app):
    return app.test_client()
