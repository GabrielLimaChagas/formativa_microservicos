import os
from flask import Flask
from flask_cors import CORS
from infrastructure.mongo_repository import MongoDBCustomerRepository
from infrastructure.event_publisher import AzureServiceBusEventPublisher
from application.use_cases import (
    ListCustomersUseCase,
    GetCustomerUseCase,
    CreateCustomerUseCase,
    UpdateCustomerUseCase,
    DeleteCustomerUseCase,
)
from presentation.controllers import create_customer_blueprint

# Instância padrão do repositório para o composition root
customer_repo = MongoDBCustomerRepository()

def create_app(repo=None):
    app = Flask(__name__)
    CORS(app)

    repository = repo or customer_repo

    # Inicializa mensageria assíncrona (Azure Service Bus com fallback in-memory)
    sb_conn = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
    sb_queue = os.getenv("AZURE_SERVICEBUS_QUEUE_NAME", "customer-events")
    event_publisher = AzureServiceBusEventPublisher(connection_string=sb_conn, queue_name=sb_queue)

    # Injeção de dependências (Composition Root)
    list_use_case = ListCustomersUseCase(repository)
    get_use_case = GetCustomerUseCase(repository)
    create_use_case = CreateCustomerUseCase(repository, event_publisher=event_publisher)
    update_use_case = UpdateCustomerUseCase(repository)
    delete_use_case = DeleteCustomerUseCase(repository)

    customer_bp = create_customer_blueprint(
        list_use_case=list_use_case,
        get_use_case=get_use_case,
        create_use_case=create_use_case,
        update_use_case=update_use_case,
        delete_use_case=delete_use_case,
    )
    app.register_blueprint(customer_bp)

    return app

app = create_app()

def init_db():
    customer_repo.seed_initial_data()

# Garante inicialização / seed do banco
init_db()

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5001))
    print(f"Customer Service iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
