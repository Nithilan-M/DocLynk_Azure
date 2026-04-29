# Remote State Backend Setup Guide for DocLynk Azure Terraform

## Overview

This guide explains how to set up and migrate Terraform state to Azure Storage Account for team collaboration and production use.

## Why Remote State?

**Local State (Default)**
- ✅ Simple for individual development
- ❌ Not suitable for teams
- ❌ No state locking (concurrent edits risk)
- ❌ Difficult to track state changes
- ❌ Hard to maintain secrets

**Remote State (Recommended)**
- ✅ Team collaboration with state locking
- ✅ Centralized audit trail
- ✅ Encrypted state in Azure
- ✅ Automatic backups
- ✅ Safe secret management

## Step-by-Step Setup

### Option 1: Automated Setup (Recommended)

```powershell
# Run the setup script
.\setup-backend.ps1

# Follow the prompts to create backend infrastructure
```

The script will:
1. Create a resource group for Terraform state
2. Create an Azure Storage Account
3. Create a blob container
4. Display the backend configuration

### Option 2: Manual Setup

#### 1. Create Resource Group

```powershell
$rg = "doclynk-tfstate-rg"
$location = "centralindia"

az group create -n $rg -l $location
```

#### 2. Create Storage Account

```powershell
$sa = "doclynktfstate123456"  # Must be globally unique, lowercase, alphanumeric only

az storage account create `
  -n $sa `
  -g $rg `
  -l $location `
  --sku Standard_LRS `
  --https-only
```

#### 3. Create Blob Container

```powershell
az storage container create `
  -n tfstate `
  --account-name $sa
```

#### 4. Enable Versioning (Optional but Recommended)

```powershell
az storage account blob-service-properties update `
  --account-name $sa `
  --enable-versioning true
```

### Step 2: Update Terraform Configuration

Edit `providers.tf` and uncomment the backend block:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "doclynk-tfstate-rg"
    storage_account_name = "doclynktfstate123456"
    container_name       = "tfstate"
    key                  = "doclynk.terraform.tfstate"
  }
}
```

### Step 3: Reinitialize Terraform

```powershell
cd modern-azure/infra/terraform
terraform init
```

When prompted: `Do you want to copy existing state to the new backend?`
Answer: **yes**

Terraform will:
1. Detect your existing local state
2. Upload it to Azure Storage
3. Configure your local environment to use remote state

### Step 4: Verify Migration

```powershell
# Verify state is in remote backend
az storage blob list -c tfstate --account-name doclynktfstate123456

# Check terraform state
terraform state list

# View remote state details
terraform state show azurerm_resource_group.main
```

## State File Location

- **Local**: `modern-azure/infra/terraform/terraform.tfstate`
- **Remote**: `{storage-account-name}/tfstate/doclynk.terraform.tfstate`
- **Backup**: Automatic backups in Azure (if versioning enabled)

## Team Collaboration

Once remote state is configured:

### Team Member Setup

```powershell
# New team member clones repo
git clone <repo-url>
cd modern-azure/infra/terraform

# Initialize Terraform (connects to remote backend)
terraform init
# Terraform automatically detects backend.azurerm block

# Verify access
terraform state list
```

### Concurrent Access Prevention

Azure Storage provides **state locking** to prevent concurrent edits:

```powershell
# When you run terraform apply, Terraform automatically:
# 1. Acquires a lock (stored as blob metadata)
# 2. Makes changes
# 3. Releases the lock

# If another user tries to plan/apply during your operation:
# Error: Resource state is currently locked
```

### Lock Debugging

If a lock is stuck:

```powershell
# View lock info
terraform force-unlock <LOCK_ID>
```

## Authentication

### Service Principal (CI/CD)

For GitHub Actions or other CI/CD:

```powershell
# Create service principal
az ad sp create-for-rbac `
  --name "doclynk-terraform" `
  --role "Contributor" `
  --scopes "/subscriptions/{subscription-id}"

# Returns:
# {
#   "appId": "...",
#   "displayName": "...",
#   "password": "...",
#   "tenant": "..."
# }
```

Add to CI/CD secrets:
```yaml
ARM_CLIENT_ID: <appId>
ARM_CLIENT_SECRET: <password>
ARM_SUBSCRIPTION_ID: <subscription-id>
ARM_TENANT_ID: <tenant>
```

### User Authentication (Local Development)

```powershell
az login
az account set --subscription <subscription-id>
terraform init
```

## Security Best Practices

### 1. Storage Account Security

```powershell
# Enable firewall (restrict access)
az storage account update `
  -n doclynktfstate123456 `
  -g doclynk-tfstate-rg `
  --default-action Deny `
  --bypass AzureServices

# Add your IP
$myIP = (Invoke-WebRequest -Uri "https://api.ipify.org?format=json").Content | ConvertFrom-Json | Select-Object -ExpandProperty ip
az storage account network-rule add `
  -n doclynktfstate123456 `
  --ip-address "$myIP/32"
```

### 2. Encryption

State is automatically encrypted with:
- **In Transit**: HTTPS only
- **At Rest**: Azure Storage Service Encryption (SSE)

### 3. Access Control

Grant minimal permissions:

```powershell
# Assign storage blob contributor role (not full owner)
az role assignment create `
  --role "Storage Blob Data Contributor" `
  --assignee "<user-or-service-principal>" `
  --scope "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{sa}"
```

## Troubleshooting

### Issue: "Backend initialization required"

**Cause**: `.terraform/` was deleted or never initialized

**Solution**:
```powershell
terraform init
# Re-connects to existing remote backend
```

### Issue: "Error acquiring the state lock"

**Cause**: Another user is modifying infrastructure, or lock is stuck

**Solution**:
```powershell
# Wait for other user to finish, or:
terraform force-unlock <LOCK_ID>

# Check active locks
az storage blob metadata show `
  -c tfstate `
  -b doclynk.terraform.tfstate `
  --account-name doclynktfstate123456
```

### Issue: "Insufficient permissions to access state"

**Cause**: User doesn't have access to storage account

**Solution**:
```powershell
# Check current user permissions
az role assignment list `
  --assignee "$(az account show -q user.name)" `
  --scope "/subscriptions/{sub}"

# Grant permission
az role assignment create `
  --role "Storage Blob Data Contributor" `
  --assignee "$(az account show -q user.name)" `
  --scope "{storage-account-resource-id}"
```

### Issue: "Failed to read state from remote backend"

**Cause**: Network connectivity or authentication issue

**Solution**:
```powershell
# Verify Azure CLI is authenticated
az account show

# Verify storage account exists
az storage account show -n doclynktfstate123456

# Verify blob container exists
az storage container exists -n tfstate --account-name doclynktfstate123456
```

## Migration from Local to Remote

If you already have local state:

```powershell
# 1. Backup local state
Copy-Item terraform.tfstate terraform.tfstate.backup

# 2. Setup remote backend (see setup steps above)

# 3. Update providers.tf with backend block

# 4. Reinitialize
terraform init

# 5. When prompted, choose 'yes' to copy state

# 6. Verify
terraform state list

# 7. Delete local state (after verification)
Remove-Item terraform.tfstate
Remove-Item terraform.tfstate.backup
```

## Resources

- [Terraform Azure Backend Docs](https://www.terraform.io/language/settings/backends/azurerm)
- [Azure Storage Security](https://learn.microsoft.com/azure/storage/common/storage-security-guide)
- [Azure RBAC for Storage](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#storage)
