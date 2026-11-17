import os
import logging
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from infrastructure.mongo_repository import MongoCustomerRepository
from infrastructure.event_publisher import AzureServiceBusEventPublisher
from application.use_cases import (
    ListCustomersUseCase,
    GetCustomerUseCase,
    CreateCustomerUseCase,
    UpdateCustomerUseCase,
    DeleteCustomerUseCase,
    BillingRequestUseCase,
)
from presentation.controllers import create_customer_blueprint

logger = logging.getLogger(__name__)

# Instância padrão para inicialização / composition root
customer_repo = MongoCustomerRepository()

def create_app(repo=None):
    app = Flask(__name__)
    CORS(app)

    # Swagger / OpenAPI
    app.config['SWAGGER'] = {
        'title': 'Customer Service API (MongoDB)',
        'uiversion': 3,
        'specs_route': '/docs/'
    }
    Swagger(app)

    repository = repo or customer_repo

    # Mensageria Azure Service Bus (com fallback in-memory)
    sb_conn = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
    sb_queue = os.getenv("AZURE_SERVICEBUS_QUEUE_NAME", "customer-events")
    event_publisher = AzureServiceBusEventPublisher(connection_string=sb_conn, queue_name=sb_queue)

    # Injeção de dependências (Composition Root)
    list_use_case = ListCustomersUseCase(repository)
    get_use_case = GetCustomerUseCase(repository)
    create_use_case = CreateCustomerUseCase(repository, event_publisher=event_publisher)
    update_use_case = UpdateCustomerUseCase(repository)
    delete_use_case = DeleteCustomerUseCase(repository)
    billing_use_case = BillingRequestUseCase(repository, event_publisher=event_publisher)

    customer_bp = create_customer_blueprint(
        list_use_case=list_use_case,
        get_use_case=get_use_case,
        create_use_case=create_use_case,
        update_use_case=update_use_case,
        delete_use_case=delete_use_case,
        billing_use_case=billing_use_case,
        repository=repository,
    )
    app.register_blueprint(customer_bp)
    app.customer_repo = repository

    return app

app = create_app()

def init_db():
    try:
        customer_repo.seed_initial_data()
        logger.info("Banco de dados MongoDB do Customer Service inicializado / seed executado.")
    except Exception as e:
        logger.error(f"Erro ao executar seed inicial do MongoDB: {e}")

init_db()

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5001))
    print(f"Customer Service (MongoDB) iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
