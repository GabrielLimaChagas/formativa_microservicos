import os
import logging
from flask import Flask
from flask_cors import CORS
from infrastructure.database import db
from infrastructure.models import CustomerModel
from infrastructure.sql_repository import SQLAlchemyCustomerRepository
from infrastructure.event_publisher import AzureServiceBusEventPublisher
from application.use_cases import (
    ListCustomersUseCase,
    GetCustomerUseCase,
    CreateCustomerUseCase,
    UpdateCustomerUseCase,
    DeleteCustomerUseCase,
)
from presentation.controllers import create_customer_blueprint

logger = logging.getLogger(__name__)

# Instância padrão do repositório para o composition root
customer_repo = SQLAlchemyCustomerRepository()

def create_app(database_uri=None, repo=None):
    app = Flask(__name__)
    CORS(app)

    # 1. Configuração do Banco de Dados: Azure SQL Database vs Fallback Local
    azure_sql_uri = os.getenv("AZURE_SQL_CONNECTION_STRING")
    basedir = os.path.abspath(os.path.dirname(__file__))
    fallback_uri = f"sqlite:///{os.path.join(basedir, 'customers.db')}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or azure_sql_uri or os.getenv("DATABASE_URL", fallback_uri)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    db.init_app(app)

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
    app.customer_repo = repository

    return app

app = create_app()

def init_db():
    with app.app_context():
        try:
            db.create_all()
            customer_repo.seed_initial_data()
            logger.info("Banco de dados do Customer Service inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados do Customer Service: {e}")

# Garante inicialização / seed do banco
init_db()

# Backward compatibility para imports externos legados caso existam
Customer = CustomerModel

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5001))
    print(f"Customer Service iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
