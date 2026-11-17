# CRMaster — Backend Microsserviços (Clean Architecture & SOLID)

Repositório dos microsserviços de backend da plataforma **CRMaster** (`customer-service` e `product-service`), desenvolvidos em **Python / Flask** estruturados rigorosamente em **Clean Architecture**, princípios **SOLID**, padrão **Database-per-Service** e mensageria assíncrona orientada a eventos via **Azure Service Bus**.

Consulte a documentação técnica completa em [docs/arc42.md](file:///c:/Users/Gabriel%20Faculdade/PUCPR/Projects/arquitetura/formativa_microservicos/docs/arc42.md).

---

## 👥 Integrantes do Grupo
* **Cauã Kammler**
* **Gabriel de Lima Chagas**
* **Vinicius Soares da Silva**

---

## 🏛️ Resumo Arquitetural
Cada microsserviço é decomposto estritamente nas camadas da Clean Architecture:
* **`domain/`:** Entidades puras de negócio (`Customer`, `Product`) com regras de validação invariantes e exceções de domínio customizadas, totalmente desacopladas de frameworks.
* **`application/`:** Casos de uso (`List`, `Get`, `Create`, `Update`, `Delete`), DTOs de entrada e saída, e interfaces abstratas (`CustomerRepository`, `ProductRepository`, `EventPublisher`, `EventConsumer`).
* **`infrastructure/`:** Adaptadores de banco de dados heterogêneos:
  * `customer-service` $\rightarrow$ **MongoDB / Azure Cosmos DB (API MongoDB)** via `pymongo`.
  * `product-service` $\rightarrow$ **Azure SQL Database / SQL Server** via `pyodbc` / SQLAlchemy (com preços em centavos).
  * Mensageria corporativa $\rightarrow$ **Azure Service Bus** (com fallback automático em memória para testes locais).
* **`presentation/`:** Blueprints Flask sem SQL e sem regras de domínio, mapeando exceções em códigos de status HTTP (`200`, `201`, `400`, `404`).
* **`app.py`:** Composition Root responsável pela instanciação das dependências concretas e injeção nos construtores dos casos de uso.

---

## 🚀 Como Rodar Localmente

### Pré-requisitos
* Python 3.11+ e pip.
* Docker (opcional para rodar o MongoDB local).

### Passo a Passo

1. **Instalação das dependências:**
   ```bash
   cd formativa_microservicos
   python -m venv venv
   # No Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # No Linux/Mac:
   source venv/bin/activate

   pip install -r requirements.txt
   pip install -r tests/requirements-test.txt
   ```

2. **Configuração de Variáveis de Ambiente:**
   Copie os exemplos `.env.example` em cada serviço:
   * **Customer Service (`customer-service/.env`):**
     ```env
     PORT=5001
     MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
     MONGODB_DATABASE=customers_db
     AZURE_SERVICEBUS_CONNECTION_STRING=
     AZURE_SERVICEBUS_QUEUE_NAME=customer-events
     ```
   * **Product Service (`product-service/.env`):**
     ```env
     PORT=5002
     # Se vazio, utiliza SQLite local transparente para dev
     AZURE_SQL_CONNECTION_STRING=
     DATABASE_URL=sqlite:///products.db
     AZURE_SERVICEBUS_CONNECTION_STRING=
     AZURE_SERVICEBUS_QUEUE_NAME=customer-events
     ```

3. **Execução dos Serviços:**
   Em terminais distintos:
   ```bash
   # Terminal 1: Customer Service
   cd customer-service
   python app.py # Roda em http://localhost:5001

   # Terminal 2: Product Service
   cd product-service
   python app.py # Roda em http://localhost:5002
   ```

4. **Execução das Suítes de Testes Automatizados:**
   ```bash
   # 1. Testes de Regressão e Fluxo de Mensageria
   python test_services.py

   # 2. Fitness Functions de Arquitetura e Isolamento de Bancos
   python -m pytest tests/ -v

   # 3. Testes Unitários com Mocks
   python -m pytest customer-service/tests/ -v
   python -m pytest product-service/tests/ -v
   ```

---

## 🌐 Links de Produção na Azure & Swagger
* **Customer Service (Azure App Service):** [https://formativa-customer-service.azurewebsites.net](https://formativa-customer-service.azurewebsites.net)
* **Product Service (Azure App Service):** [https://formativa-product-service.azurewebsites.net](https://formativa-product-service.azurewebsites.net)
* **API Gateway & BFF:** [https://formativa-api-gateway.azurewebsites.net](https://formativa-api-gateway.azurewebsites.net)
* **Documentação Swagger/OpenAPI:** [https://formativa-api-gateway.azurewebsites.net/api/docs](https://formativa-api-gateway.azurewebsites.net/api/docs) *(Placeholder)*

---

## 📹 Vídeo Demonstrativo (YouTube - Não Listado)
* **Link do Vídeo:** `https://www.youtube.com/watch?v=SEU_LINK_AQUI` *(Inserir link do YouTube não listado)*

### Checklist Roteirizado para Gravação:
1. **Apresentação Inicial:** Todos os integrantes (`Cauã Kammler`, `Gabriel de Lima Chagas` e `Vinicius Soares da Silva`) com câmeras abertas e identificação do projeto.
2. **Navegação no Frontend em Nuvem:** Acessar o Azure Static Web Apps, exibir o **Dashboard** com os cards preenchidos via retorno único do BFF (`/api/summary`).
3. **Autenticação JWT:** Demonstrar a validação de sessão e o envio do Bearer token nas chamadas de rede (DevTools).
4. **CRUD Completo:** Cadastrar, editar e excluir clientes e produtos, mostrando os dados refletidos no MongoDB (Azure Cosmos DB) e no Azure SQL.
5. **Mensageria Assíncrona:** Cadastrar um cliente no frontend, exibir o banner visual de publicação na fila do Azure Service Bus e comprovar o registro persistido na tabela de auditoria consultada pelo Dashboard.
