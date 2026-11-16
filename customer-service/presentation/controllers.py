from flask import Blueprint, request, jsonify
from domain.exceptions import EntityNotFoundException, ValidationException
from application.dtos import CreateCustomerDTO, UpdateCustomerDTO
from application.use_cases import (
    ListCustomersUseCase,
    GetCustomerUseCase,
    CreateCustomerUseCase,
    UpdateCustomerUseCase,
    DeleteCustomerUseCase,
)

def create_customer_blueprint(
    list_use_case: ListCustomersUseCase,
    get_use_case: GetCustomerUseCase,
    create_use_case: CreateCustomerUseCase,
    update_use_case: UpdateCustomerUseCase,
    delete_use_case: DeleteCustomerUseCase,
) -> Blueprint:
    bp = Blueprint("customers", __name__)

    @bp.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "UP", "service": "customer-service"}), 200

    @bp.route("/customers", methods=["GET"])
    def get_customers():
        customers = list_use_case.execute()
        return jsonify([c.to_dict() for c in customers]), 200

    @bp.route("/customers/<int:customer_id>", methods=["GET"])
    def get_customer(customer_id):
        try:
            customer = get_use_case.execute(customer_id)
            return jsonify(customer.to_dict()), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/customers", methods=["POST"])
    def create_customer():
        data = request.get_json() or {}
        name = data.get("name", "")
        if not name or not str(name).strip():
            return jsonify({"error": "O campo 'name' é obrigatório"}), 400

        try:
            pipelines_count = int(data.get("pipelinesCount", 0))
        except (ValueError, TypeError):
            pipelines_count = 0

        dto = CreateCustomerDTO(name=name.strip(), pipelines_count=pipelines_count)
        try:
            created = create_use_case.execute(dto)
            return jsonify(created.to_dict()), 201
        except ValidationException as e:
            return jsonify({"error": str(e)}), 400

    @bp.route("/customers/<int:customer_id>", methods=["PUT"])
    def update_customer(customer_id):
        data = request.get_json() or {}

        name = None
        if "name" in data:
            name = str(data["name"]).strip()
            if not name:
                return jsonify({"error": "O campo 'name' não pode ser vazio"}), 400

        pipelines_count = None
        if "pipelinesCount" in data:
            try:
                pipelines_count = int(data["pipelinesCount"])
            except (ValueError, TypeError):
                return jsonify({"error": "O campo 'pipelinesCount' deve ser numérico"}), 400

        dto = UpdateCustomerDTO(name=name, pipelines_count=pipelines_count)
        try:
            updated = update_use_case.execute(customer_id, dto)
            return jsonify(updated.to_dict()), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404
        except ValidationException as e:
            return jsonify({"error": str(e)}), 400

    @bp.route("/customers/<int:customer_id>", methods=["DELETE"])
    def delete_customer(customer_id):
        try:
            delete_use_case.execute(customer_id)
            return jsonify({"message": f"Cliente {customer_id} removido com sucesso"}), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    return bp
