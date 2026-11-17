import os
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from infrastructure.database import db
from infrastructure.models import CustomerModel
from infrastructure.repositories import SQLAlchemyCustomerRepository
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

def create_app(database_uri=None):
    app = Flask(__name__)
    CORS(app)

    # 1. Configuração de Banco: Azure SQL Database vs Fallback Local SQLite
    azure_sql_uri = os.getenv("AZURE_SQL_CONNECTION_STRING")
    basedir = os.path.abspath(os.path.dirname(__file__))
    fallback_uri = f"sqlite:///{os.path.join(basedir, 'customers.db')}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or azure_sql_uri or os.getenv("DATABASE_URL", fallback_uri)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # Swagger / OpenAPI
    app.config['SWAGGER'] = {
        'title': 'Customer Service API',
        'uiversion': 3,
        'specs_route': '/docs/'
    }
    Swagger(app)

    db.init_app(app)

    # Mensageria Azure Service Bus
    sb_conn = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
    sb_queue = os.getenv("AZURE_SERVICEBUS_QUEUE_NAME", "customer-events")
    event_publisher = AzureServiceBusEventPublisher(connection_string=sb_conn, queue_name=sb_queue)

    # Injeção de dependências (Composition Root)
    repository = SQLAlchemyCustomerRepository()
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
    )
    app.register_blueprint(customer_bp)

    return app

app = create_app()

def init_db():
    with app.app_context():
        db.create_all()
        if CustomerModel.query.count() == 0:
            seed_data = [
                CustomerModel(name="Maria", pipelines_count=2),
                CustomerModel(name="Antônio", pipelines_count=27),
            ]
            db.session.bulk_save_objects(seed_data)
            db.session.commit()
            print("Seed de dados para Clientes aplicado com sucesso!")

init_db()

Customer = CustomerModel

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5001))
    print(f"Customer Service iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
