from flask import Blueprint, request, jsonify
from infrastructure.database import db
from domain.exceptions import EntityNotFoundException, ValidationException
from application.dtos import CreateCustomerDTO, UpdateCustomerDTO
from application.use_cases import (
    ListCustomersUseCase,
    GetCustomerUseCase,
    CreateCustomerUseCase,
    UpdateCustomerUseCase,
    DeleteCustomerUseCase,
    BillingRequestUseCase,
)

def create_customer_blueprint(
    list_use_case: ListCustomersUseCase,
    get_use_case: GetCustomerUseCase,
    create_use_case: CreateCustomerUseCase,
    update_use_case: UpdateCustomerUseCase,
    delete_use_case: DeleteCustomerUseCase,
    billing_use_case: BillingRequestUseCase = None,
) -> Blueprint:
    bp = Blueprint("customers", __name__)

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
            "service": "customer-service",
            "dialect": dialect,
            "database": {
                "status": db_status,
                "error": db_error
            }
        }), status_code

    @bp.route("/customers", methods=["GET"])
    def get_customers():
        """
        Listar todos os clientes
        ---
        tags:
          - Clientes
        responses:
          200:
            description: Lista de clientes
        """
        customers = list_use_case.execute()
        return jsonify([c.to_dict() for c in customers]), 200

    @bp.route("/customers/<int:customer_id>", methods=["GET"])
    def get_customer(customer_id):
        """
        Obter cliente por ID
        ---
        tags:
          - Clientes
        parameters:
          - name: customer_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Cliente encontrado
          404:
            description: Cliente não encontrado
        """
        try:
            customer = get_use_case.execute(customer_id)
            return jsonify(customer.to_dict()), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/customers", methods=["POST"])
    def create_customer():
        """
        Criar novo cliente
        ---
        tags:
          - Clientes
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
                pipelinesCount:
                  type: integer
        responses:
          201:
            description: Cliente criado com sucesso
          400:
            description: Dados inválidos
        """
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
        """
        Atualizar cliente
        ---
        tags:
          - Clientes
        parameters:
          - name: customer_id
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
                pipelinesCount:
                  type: integer
        responses:
          200:
            description: Cliente atualizado
          400:
            description: Dados inválidos
          404:
            description: Cliente não encontrado
        """
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
        """
        Remover cliente
        ---
        tags:
          - Clientes
        parameters:
          - name: customer_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Cliente removido com sucesso
          404:
            description: Cliente não encontrado
        """
        try:
            delete_use_case.execute(customer_id)
            return jsonify({"message": f"Cliente {customer_id} removido com sucesso"}), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/customers/<int:customer_id>/billing-request", methods=["POST"])
    def billing_request(customer_id):
        """
        Disparar solicitação de faturamento assíncrono via Azure Service Bus
        ---
        tags:
          - Faturamento & Mensageria
        parameters:
          - name: customer_id
            in: path
            type: integer
            required: true
          - in: body
            name: body
            schema:
              type: object
              properties:
                amountCents:
                  type: integer
                description:
                  type: string
        responses:
          202:
            description: Solicitação enfileirada no Service Bus
          404:
            description: Cliente não encontrado
        """
        if not billing_use_case:
            return jsonify({"error": "Billing use case não configurado"}), 500

        data = request.get_json() or {}
        amount_cents = int(data.get("amountCents", 0))
        description = str(data.get("description", ""))

        try:
            result = billing_use_case.execute(customer_id, amount_cents=amount_cents, description=description)
            return jsonify(result), 202
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    return bp
