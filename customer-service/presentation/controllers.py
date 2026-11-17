import os
import logging
import traceback
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from infrastructure.database import db
from domain.exceptions import EntityNotFoundException, ValidationException
from application.dtos import CreateCustomerDTO, UpdateCustomerDTO
from application.use_cases import (
    ListCustomersUseCase,
    GetCustomerUseCase,
    CreateCustomerUseCase,
    UpdateCustomerUseCase,
    DeleteCustomerUseCase,
)

logger = logging.getLogger("customer-service.controllers")

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
        azure_sql_set = bool(os.getenv("AZURE_SQL_CONNECTION_STRING"))
        db_uri = db.engine.url.render_as_string(hide_password=True)
        dialect = db.engine.dialect.name

        db_status = "UNKNOWN"
        db_error = None

        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            db_status = "UP"
        except Exception as e:
            db_status = "DOWN"
            db_error = str(e)
            logger.error(f"[HEALTH_CHECK_FAILED] Falha ao testar conexão com banco: {e}\n{traceback.format_exc()}")

        health_data = {
            "status": "UP" if db_status == "UP" else "DEGRADED",
            "service": "customer-service",
            "azureSqlConfigured": azure_sql_set,
            "dialect": dialect,
            "database": {
                "status": db_status,
                "engineUrl": db_uri,
                "error": db_error
            }
        }
        status_code = 200 if db_status == "UP" else 503
        return jsonify(health_data), status_code

    @bp.route("/customers", methods=["GET"])
    def get_customers():
        try:
            customers = list_use_case.execute()
            return jsonify([c.to_dict() for c in customers]), 200
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"[GET /customers FAILED] Erro ao listar clientes: {e}\n{tb}")
            return jsonify({"error": "Erro ao consultar clientes no banco de dados", "detail": str(e)}), 500

    @bp.route("/customers/<string:customer_id>", methods=["GET"])
    def get_customer(customer_id):
        try:
            customer = get_use_case.execute(customer_id)
            return jsonify(customer.to_dict()), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"[GET /customers/{customer_id} FAILED]: {e}\n{tb}")
            return jsonify({"error": "Erro ao buscar cliente", "detail": str(e)}), 500

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
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"[POST /customers FAILED]: {e}\n{tb}")
            return jsonify({"error": "Erro ao criar cliente", "detail": str(e)}), 500

    @bp.route("/customers/<string:customer_id>", methods=["PUT"])
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
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"[PUT /customers/{customer_id} FAILED]: {e}\n{tb}")
            return jsonify({"error": "Erro ao atualizar cliente", "detail": str(e)}), 500

    @bp.route("/customers/<string:customer_id>", methods=["DELETE"])
    def delete_customer(customer_id):
        try:
            delete_use_case.execute(customer_id)
            return jsonify({"message": f"Cliente {customer_id} removido com sucesso"}), 200
        except EntityNotFoundException as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"[DELETE /customers/{customer_id} FAILED]: {e}\n{tb}")
            return jsonify({"error": "Erro ao remover cliente", "detail": str(e)}), 500

    return bp

