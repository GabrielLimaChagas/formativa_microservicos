from flask import Blueprint, request, jsonify
from infrastructure.database import db
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
    event_consumer = None,
) -> Blueprint:
    bp = Blueprint("products", __name__)

    @bp.route("/health", methods=["GET"])
    def health():
        """
        Health check detalhado do serviço e banco de dados
        ---
        tags:
          - Health
        responses:
          200:
            description: Serviço e banco de dados operacionais
          503:
            description: Falha na conexão com banco de dados
        """
        db_status = "UP"
        db_error = None
        dialect = "unknown"
        status_code = 200

        try:
            with db.engine.connect() as conn:
                dialect = db.engine.dialect.name
        except Exception as e:
            db_status = "DOWN"
            db_error = str(e)
            status_code = 503

        overall_status = "UP" if db_status == "UP" else "DEGRADED"

        return jsonify({
            "status": overall_status,
            "service": "product-service",
            "dialect": dialect,
            "database": {
                "status": db_status,
                "error": db_error
            }
        }), status_code

    @bp.route("/products", methods=["GET"])
    def get_products():
        """
        Listar todos os produtos
        ---
        tags:
          - Produtos
        responses:
          200:
            description: Lista de produtos
        """
        products = list_use_case.execute()
        return jsonify([p.to_dict() for p in products]), 200

    @bp.route("/products/<int:product_id>", methods=["GET"])
    def get_product(product_id):
        """
        Obter produto por ID
        ---
        tags:
          - Produtos
        parameters:
          - name: product_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Produto encontrado
          404:
            description: Produto não encontrado
        """
        try:
            product = get_use_case.execute(product_id)
            return jsonify(product.to_dict()), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/products", methods=["POST"])
    def create_product():
        """
        Criar novo produto
        ---
        tags:
          - Produtos
        parameters:
          - in: body
            name: body
            schema:
              type: object
              required:
                - name
              properties:
                name:
                  type: string
                price:
                  type: integer
        responses:
          201:
            description: Produto cadastrado com sucesso
          400:
            description: Dados inválidos
        """
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
        """
        Atualizar produto
        ---
        tags:
          - Produtos
        parameters:
          - name: product_id
            in: path
            type: integer
            required: true
          - in: body
            name: body
            schema:
              type: object
              properties:
                name:
                  type: string
                price:
                  type: integer
        responses:
          200:
            description: Produto atualizado
          400:
            description: Dados inválidos
          404:
            description: Produto não encontrado
        """
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
        """
        Remover produto
        ---
        tags:
          - Produtos
        parameters:
          - name: product_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Produto removido com sucesso
          404:
            description: Produto não encontrado
        """
        try:
            delete_use_case.execute(product_id)
            return jsonify({"message": f"Produto {product_id} removido com sucesso"}), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    # ==================== AUDITORIA / EVENTOS CONSUMIDOS ====================
    @bp.route("/audit-logs", methods=["GET"])
    def get_audit_logs():
        """
        Consultar histórico de eventos auditados da mensageria
        ---
        tags:
          - Auditoria & Mensageria
        responses:
          200:
            description: Lista de eventos processados
        """
        if audit_service:
            logs = audit_service.get_logs()
            return jsonify(logs), 200
        return jsonify([]), 200

    @bp.route("/products/process-queue", methods=["POST"])
    def process_queue_on_demand():
        """
        Processar mensagens pendentes da fila customer-events sob demanda
        ---
        tags:
          - Auditoria & Mensageria
        responses:
          200:
            description: Mensagens processadas da fila
        """
        if event_consumer and hasattr(event_consumer, "drain_queue_once"):
            count = event_consumer.drain_queue_once(max_messages=10)
            return jsonify({"status": "SUCCESS", "messagesProcessed": count}), 200
        return jsonify({"status": "IDLE", "messagesProcessed": 0, "note": "Sem conexão remota de fila ativa"}), 200

    return bp
