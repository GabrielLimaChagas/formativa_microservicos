from flask import Blueprint, request, jsonify
from domain.exceptions import EntityNotFoundException, ValidationException
from application.dtos import CreateProductDTO, UpdateProductDTO
from application.use_cases import (
    ListProductsUseCase,
    GetProductUseCase,
    CreateProductUseCase,
    UpdateProductUseCase,
    DeleteProductUseCase,
)
from application.events import AuditService

def create_product_blueprint(
    list_use_case: ListProductsUseCase,
    get_use_case: GetProductUseCase,
    create_use_case: CreateProductUseCase,
    update_use_case: UpdateProductUseCase,
    delete_use_case: DeleteProductUseCase,
    audit_service: AuditService = None,
) -> Blueprint:
    bp = Blueprint("products", __name__)

    @bp.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "UP", "service": "product-service"}), 200

    @bp.route("/products", methods=["GET"])
    def get_products():
        products = list_use_case.execute()
        return jsonify([p.to_dict() for p in products]), 200

    @bp.route("/products/<int:product_id>", methods=["GET"])
    def get_product(product_id):
        try:
            product = get_use_case.execute(product_id)
            return jsonify(product.to_dict()), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/products", methods=["POST"])
    def create_product():
        data = request.get_json() or {}
        name = data.get("name", "")
        if not name or not str(name).strip():
            return jsonify({"error": "O campo 'name' é obrigatório"}), 400

        raw_price = data.get("price", 0)
        try:
            price = int(float(raw_price))
        except (ValueError, TypeError):
            return jsonify({"error": "O campo 'price' deve ser numérico"}), 400

        dto = CreateProductDTO(name=name.strip(), price=price)
        try:
            created = create_use_case.execute(dto)
            return jsonify(created.to_dict()), 201
        except ValidationException as e:
            return jsonify({"error": str(e)}), 400

    @bp.route("/products/<int:product_id>", methods=["PUT"])
    def update_product(product_id):
        data = request.get_json() or {}

        name = None
        if "name" in data:
            name = str(data["name"]).strip()
            if not name:
                return jsonify({"error": "O campo 'name' não pode ser vazio"}), 400

        price = None
        if "price" in data:
            try:
                price = int(float(data["price"]))
            except (ValueError, TypeError):
                return jsonify({"error": "O campo 'price' deve ser numérico"}), 400

        dto = UpdateProductDTO(name=name, price=price)
        try:
            updated = update_use_case.execute(product_id, dto)
            return jsonify(updated.to_dict()), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404
        except ValidationException as e:
            return jsonify({"error": str(e)}), 400

    @bp.route("/products/<int:product_id>", methods=["DELETE"])
    def delete_product(product_id):
        try:
            delete_use_case.execute(product_id)
            return jsonify({"message": f"Produto {product_id} removido com sucesso"}), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    # ==================== AUDITORIA / EVENTOS CONSUMIDOS ====================
    @bp.route("/audit-logs", methods=["GET"])
    def get_audit_logs():
        """Retorna eventos recebidos e persistidos para auditoria/rastreamento assíncrono."""
        if audit_service:
            logs = audit_service.get_logs()
            return jsonify(logs), 200
        return jsonify([]), 200

    return bp
