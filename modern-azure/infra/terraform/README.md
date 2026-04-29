# DocLynk Azure Terraform Infrastructure

This directory contains the Infrastructure-as-Code (IaC) for deploying DocLynk to Microsoft Azure using Terraform.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [State Management](#state-management)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Terraform** ≥ 1.5
  - [Install Terraform](https://www.terraform.io/downloads.html)
  - Verify: `terraform version`

- **Azure CLI** ≥ 2.50
  - [Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
  - Verify: `az --version`

- **PowerShell 5.1+** (on Windows)
  - Included with Windows 10+

### Azure Subscription

- Active Azure subscription with appropriate permissions
- Azure CLI authenticated: `az login`
- Subscription ID from: `az account show --query id -o tsv`

---

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd modern-azure/infra/terraform
```

### 2. Initialize Terraform

```bash
# Download required providers and modules
terraform init
```

Expected output:
```
Terraform has been successfully configured!
```

### 3. Setup Variables

```bash
# Copy the example template
Copy-Item terraform.tfvars.example terraform.tfvars  # PowerShell
# or
cp terraform.tfvars.example terraform.tfvars  # Bash

# Edit with your values
notepad terraform.tfvars  # PowerShell
# or
vim terraform.tfvars  # Bash
```

**Critical Variables to Set:**
- `subscription_id`: Your Azure subscription ID
- `mysql_admin_password`: Strong password for MySQL (min 8 chars, mixed case, symbols)
- `jwt_secret_key`: 64-char hex string (generate: `openssl rand -hex 32`)
- `otp_secret_key`: 64-char hex string
- `resend_api_key`: API key from [Resend](https://resend.com)

### 4. Validate Configuration

```bash
# Check for syntax errors
terraform validate

# See what will be created
terraform plan -out=tfplan
```

### 5. Deploy

```bash
# Apply the plan
terraform apply tfplan

# Or apply interactively (requires 'yes' confirmation)
terraform apply
```

---

## Configuration

### Files Structure

```
terraform/
├── README.md                    # This file
├── providers.tf               # Provider configuration & requirements
├── main.tf                    # Resource definitions
├── variables.tf               # Input variable declarations
├── outputs.tf                 # Output definitions
├── terraform.tfvars.example   # Example values (commit to git)
├── terraform.tfvars           # Actual values (git-ignored)
└── .terraform/               # Cached providers (git-ignored)
```

### Key Variables

| Variable | Purpose | Type | Required | Notes |
|----------|---------|------|----------|-------|
| `subscription_id` | Azure subscription | `string` | ✅ | Get via `az account show -q id` |
| `environment` | Deployment environment | `string` | ❌ | Default: `prod` → Options: `dev`, `staging`, `prod` |
| `location` | Primary Azure region | `string` | ❌ | Default: `centralindia` |
| `mysql_admin_password` | Database admin password | `string` | ✅ | Min 8 chars, requires uppercase, lowercase, digits, symbols |
| `jwt_secret_key` | JWT signing key | `string` | ✅ | 64-char hex, generate: `openssl rand -hex 32` |
| `enable_monitoring` | Deploy monitoring stack | `bool` | ❌ | Default: `true` |

### Creating Environment-Specific Configs

For multiple environments, create separate `.tfvars` files:

```bash
# Development
terraform apply -var-file=dev.tfvars

# Staging
terraform apply -var-file=staging.tfvars

# Production
terraform apply -var-file=prod.tfvars
```

Example `dev.tfvars`:
```hcl
subscription_id         = "47bc037a-7fb4-43d0-b1a5-2cf5be815f20"
environment             = "dev"
location                = "centralindia"
resource_group_name     = "doclynk-dev-rg"
mysql_admin_password    = "Dev@Secure2024"
jwt_secret_key          = "8ede708b5f898180cbcf029f904de3f6b3d05bb4189fef92074f103e02a4d99d"
otp_secret_key          = "8ede708b5f898180cbcf029f904de3f6b3d05bb4189fef92074f103e02a4d99d"
resend_api_key          = "re_xxx..."
enable_monitoring       = false  # Cost savings for dev
```

---

## State Management

### Current State (Local)

By default, Terraform state is stored locally in `terraform.tfstate`.

**⚠️ WARNING**: Local state is not suitable for team collaboration. For team use, proceed to remote state setup.

### Remote State Setup (Recommended)

#### Step 1: Create Storage Account for State

```bash
$rg = "doclynk-tfstate-rg"
$sa = "doclynktfstate$(Get-Random)"
$location = "centralindia"

# Create resource group
az group create -n $rg -l $location

# Create storage account
az storage account create `
  -n $sa `
  -g $rg `
  -l $location `
  --sku Standard_LRS `
  --https-only

# Create blob container
az storage container create `
  -n tfstate `
  --account-name $sa
```

#### Step 2: Uncomment Backend in `providers.tf`

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "doclynk-tfstate-rg"
    storage_account_name = "doclynktfstate123456"  # Replace with your SA name
    container_name       = "tfstate"
    key                  = "doclynk.terraform.tfstate"
  }
}
```

#### Step 3: Reinitialize Terraform

```bash
# This will migrate local state to Azure Storage
terraform init
# Answer 'yes' when prompted to copy state
```

Verify:
```bash
az storage blob list -c tfstate --account-name doclynktfstate123456
```

---

## Deployment

### Deployment Workflow

```bash
# 1. Plan changes
terraform plan -out=tfplan

# 2. Review the plan
cat tfplan  # Or use: terraform show tfplan

# 3. Apply
terraform apply tfplan

# 4. Save outputs
terraform output > outputs.json
```

### After Deployment

```bash
# Get all outputs
terraform output

# Get specific output
terraform output backend_url

# Get ACR admin password (sensitive, masked by default)
terraform output -json acr_admin_password | jq -r '.value'
```

### Destroying Infrastructure

```bash
# Plan destruction
terraform plan -destroy -out=destroy.tfplan

# Execute destruction (WARNING: This deletes all resources!)
terraform apply destroy.tfplan

# Or directly
terraform destroy
```

---

## Resources Deployed

### Core Infrastructure

| Component | Type | Description |
|-----------|------|-------------|
| Resource Group | `azurerm_resource_group` | Container for all resources |
| MySQL Server | `azurerm_mysql_flexible_server` | Managed database (v8.0.21) |
| App Service Plan | `azurerm_service_plan` | Compute for backend (Linux, B1) |
| Linux Web App | `azurerm_linux_web_app` | Backend API (Docker container) |
| Static Web App | `azurerm_static_web_app` | Frontend (React/Vite) |
| Container Registry | `azurerm_container_registry` | Docker image repository |

### Monitoring (Optional)

- Log Analytics Workspace
- Azure Managed Grafana
- Azure Monitor Workspace
- Diagnostic Settings (logs + metrics)

---

## Monitoring

### Enable Monitoring

Monitoring is enabled by default. To disable for cost savings:

```bash
terraform apply -var="enable_monitoring=false"
```

### Accessing Grafana Dashboard

After deployment:

```bash
terraform output grafana_url
```

1. Navigate to the URL
2. Sign in with your Azure credentials
3. View pre-configured dashboards for:
   - App Service CPU, memory, requests
   - MySQL query performance, connections
   - Custom application metrics

### Log Analytics Queries

```bash
# Get backend app logs
az monitor log-analytics query \
  -w $(terraform output -raw log_analytics_workspace_id) \
  -q "AppServiceConsoleLogs | top 10 by TimeGenerated desc"

# MySQL slow queries
az monitor log-analytics query \
  -w $(terraform output -raw log_analytics_workspace_id) \
  -q "MySqlSlowLogs | where query_time_ms > 1000"
```

---

## Common Tasks

### Update Backend Environment Variables

```bash
# Modify app_settings in main.tf, then:
terraform plan  # Review changes
terraform apply
```

### Scale App Service

```bash
# Change SKU (e.g., B1 → B2)
terraform apply -var="app_service_sku=B2"
```

### Backup Database

```bash
az mysql flexible-server backup create \
  -g doclynk-rg \
  -n doclynk-db
```

### Restore from Backup

```bash
az mysql flexible-server restore \
  -g doclynk-rg \
  -n doclynk-db-restored \
  --source-server doclynk-db
```

---

## Troubleshooting

### Issue: "Invalid Authentication Token"

**Cause**: Azure CLI not authenticated

**Solution**:
```bash
az logout
az login
az account set --subscription <subscription-id>
```

### Issue: "Error: updating Linux Web App"

**Cause**: Docker image pull failed or app configuration invalid

**Solution**:
```bash
# Check app logs
az webapp log tail -g doclynk-rg -n doclynk-backend-docker

# Verify ACR credentials
terraform output acr_login_server
terraform output acr_admin_username
```

### Issue: "MySQL Server Creation Timeout"

**Cause**: Resource provisioning taking too long (MySQL typically takes 5-10 mins)

**Solution**:
```bash
# Wait longer and retry
terraform apply

# Or destroy and recreate
terraform destroy -target=azurerm_mysql_flexible_server.main
terraform apply
```

### Issue: "Static Web App deployment fails"

**Cause**: Incorrect CORS origins configured

**Solution**:
```bash
# Review CORS configuration
terraform output frontend_origins

# Update if needed
terraform apply -var="frontend_origins=https://example.com,http://localhost:5173"
```

---

## Best Practices

### ✅ Do's

- ✅ Commit `terraform.tfvars.example` (without secrets)
- ✅ Use `.gitignore` to exclude `terraform.tfvars`
- ✅ Run `terraform validate` before committing
- ✅ Use `terraform fmt` to format files
- ✅ Review `terraform plan` output carefully
- ✅ Use remote state for team environments
- ✅ Tag all resources for cost tracking
- ✅ Enable monitoring for production

### ❌ Don'ts

- ❌ Commit `terraform.tfvars` (contains secrets)
- ❌ Commit `.terraform/` directory
- ❌ Manually edit Azure resources created by Terraform
- ❌ Store state files in git
- ❌ Use identical passwords across environments
- ❌ Deploy without reviewing `terraform plan`
- ❌ Run `terraform destroy` in production without backups

---

## Additional Resources

- [Terraform Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure Naming Conventions](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/naming-and-tagging)
- [Terraform Best Practices](https://www.terraform.io/language/modules/develop#best-practices)

---

## Support

For issues or questions:
1. Check the **Troubleshooting** section
2. Review [Terraform Logs](#logging): `TF_LOG=DEBUG terraform plan`
3. Check Azure portal for resource-specific errors
4. Review [Azure CLI diagnostics](https://learn.microsoft.com/en-us/cli/azure/diagnose)

