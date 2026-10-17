import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import db
from models import Customer

app = Flask(__name__)
CORS(app)

# Database per service: SQLite isolado para Clientes
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'customers.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def init_db():
    with app.app_context():
        db.create_all()
        # Seed inicial se banco estiver vazio
        if Customer.query.count() == 0:
            seed_data = [
                Customer(name="Maria", pipelines_count=2),
                Customer(name="Antônio", pipelines_count=27),
            ]
            db.session.bulk_save_objects(seed_data)
            db.session.commit()
            print("Seed de dados para Clientes aplicado com sucesso!")

# Garante inicialização do banco mesmo ao executar via Gunicorn/App Service
init_db()

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP", "service": "customer-service"}), 200

# CRUD: Listar todos os clientes
@app.route("/customers", methods=["GET"])
def get_customers():
    customers = Customer.query.all()
    return jsonify([c.to_dict() for c in customers]), 200

# CRUD: Obter cliente por ID
@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Cliente não encontrado"}), 404
    return jsonify(customer.to_dict()), 200

# CRUD: Criar novo cliente
@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "O campo 'name' é obrigatório"}), 400

    try:
        pipelines_count = int(data.get("pipelinesCount", 0))
    except (ValueError, TypeError):
        pipelines_count = 0

    new_customer = Customer(name=name, pipelines_count=pipelines_count)
    db.session.add(new_customer)
    db.session.commit()
    return jsonify(new_customer.to_dict()), 201

# CRUD: Atualizar cliente
@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Cliente não encontrado"}), 404

    data = request.get_json() or {}
    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return jsonify({"error": "O campo 'name' não pode ser vazio"}), 400
        customer.name = name

    if "pipelinesCount" in data:
        try:
            customer.pipelines_count = int(data["pipelinesCount"])
        except (ValueError, TypeError):
            return jsonify({"error": "O campo 'pipelinesCount' deve ser numérico"}), 400

    db.session.commit()
    return jsonify(customer.to_dict()), 200

# CRUD: Excluir cliente
@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Cliente não encontrado"}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Cliente {customer_id} removido com sucesso"}), 200

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5001))
    print(f"Customer Service iniciado na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
