import pytest
from domain.entities import Customer
from infrastructure.models import CustomerModel

def test_sql_repository_crud(app, repository):
    with app.app_context():
        # 1. Inicia vazio
        assert repository.count() == 0
        assert repository.get_all() == []

        # 2. Create
        new_customer = Customer(id=None, name="Empresa XPTO", pipelines_count=3)
        created = repository.create(new_customer)
        assert created.id is not None
        assert created.name == "Empresa XPTO"
        assert created.pipelines_count == 3
        assert repository.count() == 1

        # 3. Get by ID
        found = repository.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == "Empresa XPTO"
        assert found.pipelines_count == 3

        # 4. Get by non-existing ID / invalid ID
        assert repository.get_by_id("99999") is None
        assert repository.get_by_id("invalid-id") is None

        # 5. Update
        found.update(name="Empresa XPTO Atualizada", pipelines_count=10)
        updated = repository.update(found)
        assert updated.name == "Empresa XPTO Atualizada"
        assert updated.pipelines_count == 10

        refetched = repository.get_by_id(created.id)
        assert refetched.name == "Empresa XPTO Atualizada"
        assert refetched.pipelines_count == 10

        # Update com ID inexistente ou inválido não quebra
        dummy = Customer(id="8888", name="Fake", pipelines_count=1)
        assert repository.update(dummy).id == "8888"
        dummy_invalid = Customer(id="abc", name="Fake", pipelines_count=1)
        assert repository.update(dummy_invalid).id == "abc"

        # 6. Get all
        all_customers = repository.get_all()
        assert len(all_customers) == 1
        assert all_customers[0].id == created.id

        # 7. Delete
        assert repository.delete(created.id) is True
        assert repository.count() == 0
        assert repository.get_by_id(created.id) is None

        # Delete ID não existente ou inválido
        assert repository.delete("99999") is False
        assert repository.delete("invalid-id") is False

def test_sql_repository_seed_initial_data_idempotency(app, repository):
    with app.app_context():
        assert repository.count() == 0

        # Primeira execução do seed
        repository.seed_initial_data()
        assert repository.count() == 2
        customers_first = repository.get_all()
        names_first = [c.name for c in customers_first]
        assert "Maria" in names_first
        assert "Antônio" in names_first

        # Segunda execução: deve ser idempotente (não duplica dados)
        repository.seed_initial_data()
        assert repository.count() == 2
        customers_second = repository.get_all()
        assert len(customers_second) == 2
