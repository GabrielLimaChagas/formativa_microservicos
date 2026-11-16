import os
from flask import Flask
from flask_cors import CORS
from infrastructure.database import db
from infrastructure.models import CustomerModel
from infrastructure.repositories import SQLAlchemyCustomerRepository
from application.use_cases import (
    ListCustomersUseCase,
    GetCustomerUseCase,
    CreateCustomerUseCase,
    UpdateCustomerUseCase,
    DeleteCustomerUseCase,
)
from presentation.controllers import create_customer_blueprint

def create_app(database_uri=None):
    app = Flask(__name__)
    CORS(app)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'customers.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Injeção de dependências (Composition Root)
    customer_repo = SQLAlchemyCustomerRepository()
    list_use_case = ListCustomersUseCase(customer_repo)
    get_use_case = GetCustomerUseCase(customer_repo)
    create_use_case = CreateCustomerUseCase(customer_repo)
    update_use_case = UpdateCustomerUseCase(customer_repo)
    delete_use_case = DeleteCustomerUseCase(customer_repo)

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
    with app.app_context():
        db.create_all()
        # Seed inicial se banco estiver vazio
        if CustomerModel.query.count() == 0:
            seed_data = [
                CustomerModel(name="Maria", pipelines_count=2),
                CustomerModel(name="Antônio", pipelines_count=27),
            ]
            db.session.bulk_save_objects(seed_data)
            db.session.commit()
            print("Seed de dados para Clientes aplicado com sucesso!")

# Garante inicialização do banco mesmo ao executar via Gunicorn/App Service
init_db()

# Backward compatibility para imports externos legados caso existam
Customer = CustomerModel

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5001))
    print(f"Customer Service iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
