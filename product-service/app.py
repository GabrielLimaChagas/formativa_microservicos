import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import db
from models import Product

app = Flask(__name__)
CORS(app)

# Database per service: SQLite isolado para Produtos
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'products.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def init_db():
    with app.app_context():
        db.create_all()
        # Seed inicial se banco estiver vazio
        if Product.query.count() == 0:
            seed_data = [
                Product(name="Roçadeira Stihl", price=25999),
                Product(name="Óleo 2T", price=3299),
            ]
            db.session.bulk_save_objects(seed_data)
            db.session.commit()
            print("Seed de dados para Produtos aplicado com sucesso!")

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP", "service": "product-service"}), 200

# CRUD: Listar todos os produtos
@app.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products]), 200

# CRUD: Obter produto por ID
@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produto não encontrado"}), 404
    return jsonify(product.to_dict()), 200

# CRUD: Criar novo produto
@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "O campo 'name' é obrigatório"}), 400

    raw_price = data.get("price", 0)
    try:
        # Se vier em formato numérico ou float ou string
        price = int(float(raw_price))
    except (ValueError, TypeError):
        return jsonify({"error": "O campo 'price' deve ser numérico"}), 400

    new_product = Product(name=name, price=price)
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201

# CRUD: Atualizar produto
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produto não encontrado"}), 404

    data = request.get_json() or {}
    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return jsonify({"error": "O campo 'name' não pode ser vazio"}), 400
        product.name = name

    if "price" in data:
        try:
            product.price = int(float(data["price"]))
        except (ValueError, TypeError):
            return jsonify({"error": "O campo 'price' deve ser numérico"}), 400

    db.session.commit()
    return jsonify(product.to_dict()), 200

# CRUD: Excluir produto
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produto não encontrado"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"Produto {product_id} removido com sucesso"}), 200

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5002))
    print(f"Product Service iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
