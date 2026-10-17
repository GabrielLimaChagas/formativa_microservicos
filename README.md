# Link do Site
https://zealous-pebble-0418eed0f.5.azurestaticapps.net/produtos

# Formativa - Arquitetura de Microsserviços

## 👥 Integrantes do Grupo
Consulte o arquivo [GRUPO.md](file:///c:/Users/Gabriel%20Faculdade/PUCPR/Projects/formativa_microservicos/GRUPO.md) para a lista de integrantes:
- Cauã Kammler
- Gabriel de Lima Chagas
- Vinicius Soares da Silva

---

## 🌐 Endereços em Produção (Microsoft Azure)

- **Frontend (Azure Static Web Apps):**  
  👉 [https://zealous-pebble-0418eed0f.5.azurestaticapps.net/produtos](https://zealous-pebble-0418eed0f.5.azurestaticapps.net/produtos)

- **API Gateway (Azure App Service):**  
  👉 [https://formativa-api-gateway.azurewebsites.net/api/health](https://formativa-api-gateway.azurewebsites.net/api/health)

- **Microsserviço de Clientes (Customer Service):**  
  👉 [https://formativa-customer-service.azurewebsites.net/health](https://formativa-customer-service.azurewebsites.net/health)  
  👉 [https://formativa-customer-service.azurewebsites.net/customers](https://formativa-customer-service.azurewebsites.net/customers)

- **Microsserviço de Produtos (Product Service):**  
  👉 [https://formativa-product-service.azurewebsites.net/health](https://formativa-product-service.azurewebsites.net/health)  
  👉 [https://formativa-product-service.azurewebsites.net/products](https://formativa-product-service.azurewebsites.net/products)

---

## 🏗️ Arquitetura dos Microsserviços
- **Database-per-Service:** Cada serviço possui persistência e banco isolado.
- **Resiliência e Escalabilidade:** Cada serviço roda de forma desacoplada em instâncias dedicadas no Azure App Service (Linux).
- **CORS e Integração:** Configuração de origens cruzadas e headers habilitada para comunicação direta com o Frontend.
- **CI/CD:** Pipelines automatizadas no GitHub Actions em `.github/workflows/`.
