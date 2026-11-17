from domain.entities import Product
from infrastructure.models import ProductModel, AuditLogModel
from infrastructure.database import db

def test_product_repository_crud(app, repository):
    with app.app_context():
        # 1. Inicia vazio
        assert repository.count() == 0
        assert repository.get_all() == []

        # 2. Create
        new_prod = Product(id=None, name="Martelo Teste", price=3500)
        created = repository.create(new_prod)
        assert created.id is not None
        assert created.name == "Martelo Teste"
        assert created.price == 3500
        assert repository.count() == 1

        # 3. Get by ID
        found = repository.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == "Martelo Teste"
        assert found.price == 3500

        # Inexistente
        assert repository.get_by_id(99999) is None

        # 4. Update
        found.update(name="Martelo Teste Atualizado", price=4200)
        updated = repository.update(found)
        assert updated.name == "Martelo Teste Atualizado"
        assert updated.price == 4200

        refetched = repository.get_by_id(created.id)
        assert refetched.name == "Martelo Teste Atualizado"
        assert refetched.price == 4200

        # Update com ID inexistente
        fake_prod = Product(id=8888, name="Fake", price=100)
        assert repository.update(fake_prod).id == 8888

        # 5. Get All
        items = repository.get_all()
        assert len(items) == 1
        assert items[0].id == created.id

        # 6. Delete
        assert repository.delete(created.id) is True
        assert repository.count() == 0
        assert repository.get_by_id(created.id) is None
        assert repository.delete(99999) is False

def test_product_and_audit_models_and_seed(app, repository):
    with app.app_context():
        # Testa tabelas criadas automaticamente
        assert ProductModel.query.count() == 0
        assert AuditLogModel.query.count() == 0

        # Teste de persistência de AuditLog
        log_entry = AuditLogModel(
            event_type="CustomerCreatedEvent",
            payload='{"customerId": "1", "name": "Maria"}'
        )
        db.session.add(log_entry)
        db.session.commit()

        assert AuditLogModel.query.count() == 1
        log_dict = log_entry.to_dict()
        assert log_dict["eventType"] == "CustomerCreatedEvent"
        assert "Maria" in log_dict["payload"]
        assert log_dict["id"] is not None

        # Teste de seed inicial e idempotência de produtos
        repository.seed_initial_data()
        assert ProductModel.query.count() == 2
        names_first = [p.name for p in ProductModel.query.all()]
        assert "Roçadeira Stihl" in names_first
        assert "Óleo 2T" in names_first

        # Segunda execução: seed deve ser idempotente
        repository.seed_initial_data()
        assert ProductModel.query.count() == 2
