# CRMaster — API Gateway & BFF

Módulo de **API Gateway & Backend-For-Frontend (BFF)** da plataforma **CRMaster**, desenvolvido em **Python / Flask** seguindo os princípios de **Clean Architecture** e **SOLID**.

Consulte a documentação técnica completa em [docs/arc42.md](file:///c:/Users/Gabriel%20Faculdade/PUCPR/Projects/arquitetura/formativa_microservicos/api-gateway/docs/arc42.md).

---

## 👥 Integrantes do Grupo
* **Cauã Kammler**
* **Gabriel de Lima Chagas**
* **Vinicius Soares da Silva**

---

## 🏛️ Resumo Arquitetural
O API Gateway atua como fronteira única de entrada e orquestrador de apresentação para os microfrontends:
* **Clean Architecture & SOLID:** Estruturado em camadas estritamente desacopladas:
  * `domain/` & `application/`: Abstrações puras (`HttpClient`, `TokenService`) e regras de agregação (`SummaryService`, `HealthService`).
  * `infrastructure/`: Implementação concreta do cliente HTTP e serviço JWT.
  * `presentation/`: Blueprints de roteamento e decorador de segurança centralizada `@require_auth`.
  * `app.py`: Composition Root para injeção de dependências.
* **Isolamento de Banco:** 100% livre de conexões com banco de dados, atuando exclusivamente como proxy reverso e agregador.
* **Segurança Centralizada:** Emissão e validação de tokens JWT (HS256) via `POST /api/auth/login` e `GET /api/auth/verify`.

---

## 🚀 Como Rodar Localmente

### Pré-requisitos
* Python 3.11+ e pip.

### Passo a Passo

1. **Instalação das dependências:**
   ```bash
   cd api-gateway
   python -m venv venv
   # No Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # No Linux/Mac:
   source venv/bin/activate

   pip install -r requirements.txt
   pip install pytest pytest-archon typeguard
   ```

2. **Configuração de Variáveis de Ambiente:**
   Copie o arquivo `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Configurações padrão:
   ```env
   PORT=5000
   CUSTOMERS_SERVICE_URL=http://localhost:5001
   PRODUCTS_SERVICE_URL=http://localhost:5002
   JWT_SECRET_KEY=secret-cloud-native-key-2026-super-secure-32bytes
   JWT_ALGORITHM=HS256
   ```

3. **Execução da Aplicação:**
   ```bash
   python app.py
   ```
   O serviço iniciará na porta `5000` (`http://localhost:5000`).

4. **Execução dos Testes Automatizados:**
   ```bash
   # Testes Unitários com Mocks e Testes de Arquitetura do Gateway
   python -m pytest tests/ -v
   ```

---

## 🌐 Links de Produção na Azure & Swagger
* **API Gateway em Produção (Azure App Service):** [https://formativa-api-gateway.azurewebsites.net](https://formativa-api-gateway.azurewebsites.net)
* **Health Check Agregado:** [https://formativa-api-gateway.azurewebsites.net/api/health](https://formativa-api-gateway.azurewebsites.net/api/health)
* **Documentação Swagger/OpenAPI:** [https://formativa-api-gateway.azurewebsites.net/api/docs](https://formativa-api-gateway.azurewebsites.net/api/docs)

---

## 📹 Vídeo Demonstrativo (YouTube - Não Listado)
* **Link do Vídeo:** [https://youtu.be/JhIgVuGcaQM](https://youtu.be/JhIgVuGcaQM)

### Checklist Roteirizado para Gravação:
1. **Apresentação Inicial:** Todos os integrantes (`Cauã Kammler`, `Gabriel de Lima Chagas` e `Vinicius Soares da Silva`) com câmeras abertas e identificação do projeto.
2. **Navegação no Frontend em Nuvem:** Acessar o Azure Static Web Apps, exibir o **Dashboard** com os cards preenchidos via retorno único do BFF (`/api/summary`).
3. **Autenticação JWT:** Demonstrar a validação de sessão e o envio do Bearer token nas chamadas de rede (DevTools).
4. **CRUD Completo:** Cadastrar, editar e excluir clientes e produtos, mostrando os dados refletidos no MongoDB (Azure Cosmos DB) e no Azure SQL.
5. **Mensageria Assíncrona:** Cadastrar um cliente no frontend, exibir o banner visual de publicação na fila do Azure Service Bus e comprovar o registro persistido na tabela de auditoria consultada pelo Dashboard.
