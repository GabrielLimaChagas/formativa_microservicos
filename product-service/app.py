import os
from flask import Flask
from flask_cors import CORS
from infrastructure.database import db
from infrastructure.models import ProductModel
from infrastructure.repositories import SQLAlchemyProductRepository
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

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'products.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Injeção de dependências (Composition Root)
    product_repo = SQLAlchemyProductRepository()
    list_use_case = ListProductsUseCase(product_repo)
    get_use_case = GetProductUseCase(product_repo)
    create_use_case = CreateProductUseCase(product_repo)
    update_use_case = UpdateProductUseCase(product_repo)
    delete_use_case = DeleteProductUseCase(product_repo)

    product_bp = create_product_blueprint(
        list_use_case=list_use_case,
        get_use_case=get_use_case,
        create_use_case=create_use_case,
        update_use_case=update_use_case,
        delete_use_case=delete_use_case,
    )
    app.register_blueprint(product_bp)

    return app

app = create_app()

def init_db():
    with app.app_context():
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
