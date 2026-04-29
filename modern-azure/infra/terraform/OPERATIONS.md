# Terraform Operations Guide for DocLynk Azure

This guide covers common Terraform operations and daily tasks.

## Table of Contents

- [Basic Commands](#basic-commands)
- [Planning & Deployment](#planning--deployment)
- [Scaling & Updates](#scaling--updates)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

---

## Basic Commands

### Initialize Terraform

```powershell
# First-time setup
terraform init

# Reinitialize (useful after updating backend)
terraform init -reconfigure

# Migrate to new backend
terraform init -migrate-state
```

### Validate Configuration

```powershell
# Check syntax and configuration
terraform validate

# Format check
terraform fmt -check

# Auto-format files
terraform fmt -recursive
```

### View Current State

```powershell
# List all resources
terraform state list

# View specific resource
terraform state show azurerm_linux_web_app.backend

# View outputs
terraform output

# Export state to JSON
terraform state pull > state-backup.json
```

---

## Planning & Deployment

### Create Execution Plan

```powershell
# Dev environment
terraform plan -var-file=dev.tfvars -out=tfplan

# Staging
terraform plan -var-file=staging.tfvars -out=tfplan

# Production
terraform plan -var-file=prod.tfvars -out=tfplan
```

### Review Plan

```powershell
# Human-readable format
terraform show tfplan

# JSON format (for scripting)
terraform show -json tfplan > tfplan.json
```

### Apply Changes

```powershell
# Apply pre-created plan
terraform apply tfplan

# Or apply interactively (requires 'yes' confirmation)
terraform apply -var-file=prod.tfvars

# Apply with auto-approval (CI/CD only!)
terraform apply -var-file=prod.tfvars -auto-approve
```

### Automatic Deployment Script

```powershell
# Deploy with safety checks
.\deploy.ps1 -Action apply -Environment prod

# Plan only
.\deploy.ps1 -Action plan -Environment staging

# Destroy (requires confirmation)
.\deploy.ps1 -Action destroy -Environment dev
```

---

## Scaling & Updates

### Scale App Service

```powershell
# Change SKU (e.g., B1 → S1 → P1v2)
terraform apply -var-file=prod.tfvars -var="app_service_sku=P1v2"

# Plan first to review
terraform plan -var-file=prod.tfvars -var="app_service_sku=P1v2"
```

### Scale Database

```powershell
# Increase storage (e.g., 100 GB → 200 GB)
terraform apply -var-file=prod.tfvars -var="mysql_storage_gb=200"

# Change SKU (e.g., B_Standard_B1ms → B_Standard_B2s)
terraform apply -var-file=prod.tfvars -var="mysql_sku_name=B_Standard_B2s"
```

### Update Backend Environment Variables

Edit `main.tf` app_settings block, then:

```powershell
terraform plan -var-file=prod.tfvars -out=tfplan
terraform show tfplan  # Review changes
terraform apply tfplan
```

### Update Container Image

```powershell
# Rebuild and push to ACR
az acr build -r doclynkregistryprod -t doclynk-backend:v2.0 ../backend/

# Trigger app service to pull new image
az webapp deployment container config `
  -n doclynk-backend-prod `
  -g doclynk-prod-rg `
  --enable-cd true
```

### Enable/Disable Monitoring

```powershell
# Enable monitoring
terraform apply -var-file=prod.tfvars -var="enable_monitoring=true"

# Disable monitoring (cost savings)
terraform apply -var-file=prod.tfvars -var="enable_monitoring=false"
```

---

## Maintenance

### Backup Database

```powershell
# Manual backup
az mysql flexible-server backup create `
  -g doclynk-prod-rg `
  -n doclynk-db-prod `
  --backup-name manual-backup-$(Get-Date -Format yyyyMMdd)

# List backups
az mysql flexible-server backup list `
  -g doclynk-prod-rg `
  -n doclynk-db-prod
```

### Restore Database from Backup

```powershell
# Restore to new server
az mysql flexible-server restore `
  -g doclynk-prod-rg `
  -n doclynk-db-restored `
  --source-server doclynk-db-prod `
  --restore-point-in-time "2024-01-15T10:00:00Z"
```

### Export State for Backup

```powershell
# Backup current state
terraform state pull > terraform.state.backup-$(Get-Date -Format yyyyMMdd).json

# Store securely!
```

### Check Resource Drift

```powershell
# Refresh state from actual Azure resources
terraform refresh -var-file=prod.tfvars

# Check for drift (manual changes in Azure portal)
terraform plan -var-file=prod.tfvars

# If drift detected, Terraform will show required corrections
```

### Update Resource Tags

```powershell
# Add or modify tags in variables or tfvars
# Then apply:
terraform plan -var-file=prod.tfvars -out=tfplan
terraform apply tfplan

# Or directly in main.tf locals section
```

---

## Troubleshooting

### Issue: "Provider configuration missing"

**Cause**: `terraform init` not run

**Solution**:
```powershell
terraform init
```

### Issue: "Azure authentication failed"

**Cause**: Not logged in to Azure CLI

**Solution**:
```powershell
az login
az account set --subscription <subscription-id>
```

### Issue: "Resource already exists in Azure"

**Cause**: Resource created outside Terraform or leftover from previous deployment

**Solution**:
```powershell
# Import existing resource
terraform import azurerm_resource_group.main /subscriptions/{sub}/resourceGroups/{rg}

# Or delete from Azure and re-create
az group delete -n doclynk-prod-rg
terraform apply -var-file=prod.tfvars
```

### Issue: "Lock timeout: state is locked"

**Cause**: Another user is modifying infrastructure

**Solution**:
```powershell
# Wait for other user to finish, or:
terraform force-unlock <LOCK_ID>

# Find lock ID from error message
```

### Issue: "Insufficient permissions"

**Cause**: User doesn't have required Azure roles

**Solution**:
```powershell
# Grant Contributor role (or more specific role)
az role assignment create `
  --role "Contributor" `
  --assignee <user-email> `
  --scope "/subscriptions/{subscription-id}"
```

### Issue: "Resource quota exceeded"

**Cause**: Azure subscription limit reached (e.g., App Service plans, databases)

**Solution**:
```powershell
# Request quota increase in Azure Portal
# Or reduce resource count/size

# Check quotas
az provider show -n Microsoft.Compute --query quotas
```

### View Detailed Logs

```powershell
# Enable debug logging
$env:TF_LOG = "DEBUG"
terraform plan -var-file=prod.tfvars

# Save logs to file
$env:TF_LOG_PATH = "terraform-debug.log"
terraform plan -var-file=prod.tfvars

# View logs
Get-Content terraform-debug.log | tail -100
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Terraform Deploy

on:
  push:
    branches: [main]
    paths:
      - 'modern-azure/infra/terraform/**'

env:
  TF_VERSION: '1.5.0'
  ARM_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  ARM_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
  ARM_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
  ARM_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        run: terraform init
        working-directory: modern-azure/infra/terraform

      - name: Terraform Plan
        run: terraform plan -var-file=prod.tfvars -out=tfplan
        working-directory: modern-azure/infra/terraform

      - name: Terraform Apply
        run: terraform apply tfplan
        working-directory: modern-azure/infra/terraform
```

---

## Reference

### Common Resources

| Resource | Variable | Usage |
|----------|----------|-------|
| Resource Group | `resource_group_name` | Container for all resources |
| App Service Plan | `app_service_sku` | Compute pricing tier |
| MySQL Database | `mysql_sku_name` | Database pricing tier |
| Container Registry | `acr_sku` | Registry pricing |
| Monitoring | `enable_monitoring` | Enable/disable Grafana |

### Useful Azure CLI Commands

```powershell
# List all resources
az resource list -g doclynk-prod-rg

# Check resource status
az webapp show -n doclynk-backend-prod -g doclynk-prod-rg

# View app logs
az webapp log tail -n doclynk-backend-prod -g doclynk-prod-rg

# Get connection string
az mysql flexible-server show-connection-string -s doclynk-db-prod -d doclynk_prod
```

---

## Best Practices Checklist

- [ ] Always run `terraform plan` before `terraform apply`
- [ ] Review plan output carefully, especially for `destroy` operations
- [ ] Use environment-specific `.tfvars` files
- [ ] Commit Terraform code to git, exclude `.tfstate` files
- [ ] Use remote state for production
- [ ] Enable state locking (automatic with remote state)
- [ ] Tag all resources for cost tracking
- [ ] Monitor Azure costs regularly
- [ ] Test changes in dev/staging before production
- [ ] Document custom modifications outside Terraform
