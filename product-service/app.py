import os
from flask import Flask
from flask_cors import CORS
from infrastructure.database import db
from infrastructure.models import ProductModel, AuditLogModel
from infrastructure.repositories import SQLAlchemyProductRepository
from infrastructure.event_consumer import AzureServiceBusEventConsumer
from application.events import AuditService
from application.use_cases import (
    ListProductsUseCase,
    GetProductUseCase,
    CreateProductUseCase,
    UpdateProductUseCase,
    DeleteProductUseCase,
)
from presentation.controllers import create_product_blueprint

def create_app(database_uri=None):
    app = Flask(__name__)
    CORS(app)

    # 1. Configuração do Banco de Dados: Azure SQL Database vs Fallback Local
    # Se AZURE_SQL_CONNECTION_STRING estiver definida, utiliza a conexão gerenciada da nuvem
    azure_sql_uri = os.getenv("AZURE_SQL_CONNECTION_STRING")
    basedir = os.path.abspath(os.path.dirname(__file__))
    fallback_uri = f"sqlite:///{os.path.join(basedir, 'products.db')}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or azure_sql_uri or os.getenv("DATABASE_URL", fallback_uri)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    db.init_app(app)

    # Injeção de dependências (Composition Root)
    product_repo = SQLAlchemyProductRepository()
    list_use_case = ListProductsUseCase(product_repo)
    get_use_case = GetProductUseCase(product_repo)
    create_use_case = CreateProductUseCase(product_repo)
    update_use_case = UpdateProductUseCase(product_repo)
    delete_use_case = DeleteProductUseCase(product_repo)

    audit_service = AuditService(db.session, AuditLogModel)

    # Inicia Consumidor Azure Service Bus
    sb_conn = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
    sb_queue = os.getenv("AZURE_SERVICEBUS_QUEUE_NAME", "customer-events")
    consumer = AzureServiceBusEventConsumer(
        connection_string=sb_conn,
        queue_name=sb_queue,
        audit_service=audit_service,
        app_context_provider=app.app_context
    )
    consumer.start_listening()
    app.event_consumer = consumer

    product_bp = create_product_blueprint(
        list_use_case=list_use_case,
        get_use_case=get_use_case,
        create_use_case=create_use_case,
        update_use_case=update_use_case,
        delete_use_case=delete_use_case,
        audit_service=audit_service,
    )
    app.register_blueprint(product_bp)

    return app

app = create_app()

def init_db(app_instance=None):
    target_app = app_instance or app
    with target_app.app_context():
        db.create_all()
        # Seed inicial se banco estiver vazio
        if ProductModel.query.count() == 0:
            seed_data = [
                ProductModel(name="Roçadeira Stihl", price=25999),
                ProductModel(name="Óleo 2T", price=3299),
            ]
            db.session.bulk_save_objects(seed_data)
            db.session.commit()
            print("Seed de dados para Produtos aplicado com sucesso!")

# Garante inicialização do banco mesmo ao executar via Gunicorn/App Service
init_db()

# Backward compatibility para imports externos legados caso existam
Product = ProductModel

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5002))
    print(f"Product Service iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
