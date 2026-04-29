# DocLynk Modern Azure

Production-ready, Azure-native rebuild of the Doc_Lynk healthcare appointment system.

## Stack
- Frontend: React + Vite + Tailwind CSS + Axios + React Router
- Backend: FastAPI + SQLAlchemy + JWT + PyMySQL
- Database: Azure Database for MySQL Flexible Server
- Containers: Docker (backend)
- CI/CD: GitHub Actions (build and push Docker image)
- Hosting: Azure Static Web Apps (frontend) + Azure Container Apps (backend)

## Folder Structure

```text
modern-azure/
  backend/
    app/
      routes/
      __init__.py
      auth.py
      database.py
      main.py
      models.py
      schemas.py
    .env.example
    Dockerfile
    requirements.txt
  frontend/
    public/
      staticwebapp.config.json
    src/
      api/
      components/
      context/
      pages/
      App.jsx
      index.css
      main.jsx
    .env.example
    index.html
    package.json
    postcss.config.js
    tailwind.config.js
    vite.config.js
  infra/
    sql/
      schema.sql

.github/
  workflows/
    backend-ci.yml
```

## Local Run

### 1. Backend

```bash
cd modern-azure/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API health check: `GET http://localhost:8000/health`

### 2. Frontend

```bash
cd modern-azure/frontend
npm install
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
npm run dev
```

App URL: `http://localhost:5173`

## Docker Run

From `modern-azure/` directory:

### 1. Production-like local run (backend + built frontend)

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8012`
- Backend health: `http://localhost:8012/health`

### 2. Frontend hot-reload mode (optional)

```bash
docker compose --profile dev up --build backend frontend-dev
```

- Frontend dev server: `http://localhost:5173`
- Backend API: `http://localhost:8012`

### 3. Stop containers

```bash
docker compose down
```

Notes:
- Backend reads environment from `backend/.env` via compose `env_file`.
- Frontend container gets `VITE_API_URL=http://localhost:8012` by default.
- If you change backend port mapping, update `VITE_API_URL` in `docker-compose.yml`.

## Azure Initialization (Database + Deployment)

Use this flow when your database is Azure MySQL Flexible Server and you deploy frontend/backend to Azure.

### 1. Prepare backend Azure env

```bash
cd modern-azure/backend
Copy-Item .env.azure.example .env
```

Set these required values in `backend/.env`:
- `DATABASE_URL` (optional; leave empty if using `DB_*` values)
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`
- `DB_SSL_MODE=require`
- `JWT_SECRET_KEY`
- `OTP_SECRET_KEY`
- `FRONTEND_ORIGINS` with your Azure Static Web App URL
- `BACKEND_PUBLIC_URL` with your Azure backend URL
- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`

### 2. Validate backend container against Azure DB locally

```bash
cd modern-azure
docker compose up --build backend
```

Health check:
- `http://localhost:8012/health`

### 3. Prepare frontend Azure env

```bash
cd modern-azure/frontend
Copy-Item .env.azure.example .env
```

Set:
- `VITE_API_URL=https://<your-azure-backend-url>`

### 4. Build frontend image (optional containerized frontend)

```bash
cd modern-azure
$env:VITE_API_URL="https://<your-azure-backend-url>"
docker compose build frontend
```

### 5. Azure deployment mapping

- Azure Database for MySQL Flexible Server: source of truth DB
- Azure App Service or Azure Container Apps (backend): use env values from `backend/.env.azure.example`
- Azure Static Web Apps (frontend): set `VITE_API_URL` in SWA configuration

### 6. CORS checklist

Ensure backend `FRONTEND_ORIGINS` includes:
- `https://<your-app>.azurestaticapps.net`
- `https://<your-custom-domain>` (if used)

## Environment Variables

### Backend (`modern-azure/backend/.env`)
- `DATABASE_URL` (optional, takes precedence over DB_* variables)
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`
- `DB_SSL_MODE`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `VERIFICATION_TOKEN_EXPIRE_MINUTES`
- `FRONTEND_ORIGINS`
- `FRONTEND_PUBLIC_URL`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `EMAIL_FALLBACK_TO_LINK` (set `false` in production)

### Frontend (`modern-azure/frontend/.env`)
- `VITE_API_URL`

## Azure Deployment

### 1. Azure MySQL Flexible Server
1. Create a MySQL Flexible Server in Azure.
2. Configure firewall rules to allow backend outbound access.
3. Create database and user.
4. Run SQL from `infra/sql/schema.sql`.

### 2. Backend to Azure App Service or Azure Container Apps
1. Build and push backend image (GitHub Action handles this on push to `main`).
2. Create your target service:
  - App Service (Web App for Containers) or
  - Container App in a Container Apps Environment
3. Set environment variables in the backend service:
   - `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`
  - `DB_SSL_MODE`
   - `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
   - `FRONTEND_ORIGINS`
4. Set health probe path to `/health`.

### 3. Frontend to Azure Static Web Apps
1. Create Static Web App and connect GitHub repo.
2. Set app location to `modern-azure/frontend`.
3. Build command: `npm run build`
4. Output location: `dist`
5. Set frontend environment variable:
   - `VITE_API_URL=<container-app-backend-url>`

## CI/CD Notes
- Workflow file: `.github/workflows/backend-ci.yml` (repository root)
- Required GitHub repository secrets:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`

## Terraform (Infrastructure as Code)

All Azure infrastructure is defined in `infra/terraform/`. Use Terraform to provision, update, or tear down the full environment reproducibly.

### Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) logged in (`az login`)

### Quick Start

```bash
cd modern-azure/infra/terraform

# 1. Copy the variables template and fill in your secrets
Copy-Item terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your passwords, API keys, subscription ID, etc.

# 2. Initialize providers
terraform init

# 3. Preview what will be created
terraform plan

# 4. Apply (creates all Azure resources)
terraform apply
```

### Resources Provisioned

| Resource | Terraform Name | Default Azure Name |
|---|---|---|
| Resource Group | `azurerm_resource_group.main` | `doclynk-rg` |
| MySQL Flexible Server | `azurerm_mysql_flexible_server.main` | `doclynk-db` |
| MySQL Database | `azurerm_mysql_flexible_database.app` | `doclynkdb` |
| Container Registry | `azurerm_container_registry.main` | `doclynkregistry` |
| App Service Plan | `azurerm_service_plan.backend` | `doclynk-backend-plan` |
| Backend Web App | `azurerm_linux_web_app.backend` | `doclynk-backend-docker` |
| Static Web App | `azurerm_static_web_app.frontend` | `doclynk-frontend` |
| Log Analytics *(optional)* | `azurerm_log_analytics_workspace.main` | `doclynk-logs` |

### Importing Existing Resources

If you already have these resources in Azure, import them into Terraform state instead of recreating:

```bash
# Example: import resource group
terraform import azurerm_resource_group.main /subscriptions/<sub-id>/resourceGroups/doclynk-rg

# Example: import MySQL server
terraform import azurerm_mysql_flexible_server.main /subscriptions/<sub-id>/resourceGroups/doclynk-rg/providers/Microsoft.DBforMySQL/flexibleServers/doclynk-db

# Example: import ACR
terraform import azurerm_container_registry.main /subscriptions/<sub-id>/resourceGroups/doclynk-rg/providers/Microsoft.ContainerRegistry/registries/doclynkregistry
```

### Key Outputs

After `terraform apply`, useful values are printed:

```bash
terraform output mysql_fqdn          # MySQL connection host
terraform output acr_login_server    # ACR URL for docker push
terraform output backend_url         # Backend App Service URL
terraform output frontend_url        # Frontend Static Web App URL
terraform output -raw frontend_api_token  # SWA deploy token for CI
```

### File Structure

```text
infra/terraform/
├── providers.tf             # Terraform & AzureRM provider config
├── variables.tf             # All input variables with defaults
├── main.tf                  # Resource definitions
├── outputs.tf               # Exported values
└── terraform.tfvars.example # Secrets template (copy → terraform.tfvars)
```

## API Endpoints
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/verify-email?token=...`
- `POST /auth/resend-verification`
- `GET /users/doctors`
- `POST /appointments`
- `GET /appointments`
- `PUT /appointments/{id}/status`
- `DELETE /appointments/{id}`
- `GET /health`
