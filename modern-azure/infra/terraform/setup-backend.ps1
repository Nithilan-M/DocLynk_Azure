# Setup Remote State Backend on Azure Storage Account
# This script creates an Azure Storage Account for Terraform state management
# Required for team collaboration and production use

param(
    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId,

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = "doclynk-tfstate-rg",

    [Parameter(Mandatory = $false)]
    [string]$StorageAccountName = "doclynktfstate$(Get-Random -Minimum 10000 -Maximum 99999)",

    [Parameter(Mandatory = $false)]
    [string]$ContainerName = "tfstate",

    [Parameter(Mandatory = $false)]
    [string]$Location = "centralindia"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
}

function Write-Info { Write-Host "[INFO]" -ForegroundColor $colors.Info -NoNewline; Write-Host " $args" }
function Write-Success { Write-Host "[SUCCESS]" -ForegroundColor $colors.Success -NoNewline; Write-Host " $args" }
function Write-Warn { Write-Host "[WARN]" -ForegroundColor $colors.Warning -NoNewline; Write-Host " $args" }
function Write-Error { Write-Host "[ERROR]" -ForegroundColor $colors.Error -NoNewline; Write-Host " $args"; exit 1 }

# ────────────────────────────────────────────────────────────
# Prerequisites Check
# ────────────────────────────────────────────────────────────

Write-Info "Checking prerequisites..."

# Check Azure CLI
$azVersion = az --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Azure CLI not found. Install from: https://learn.microsoft.com/cli/azure/install-azure-cli"
}
Write-Success "Azure CLI found"

# Check authentication
$currentAz = az account show --query name -o tsv 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Not authenticated to Azure. Running 'az login'..."
    az login | Out-Null
}
Write-Success "Authenticated as: $currentAz"

# Get subscription ID if not provided
if (-not $SubscriptionId) {
    $SubscriptionId = az account show --query id -o tsv
}

Write-Info "Using subscription: $SubscriptionId"
az account set --subscription $SubscriptionId

# ────────────────────────────────────────────────────────────
# Create Resource Group
# ────────────────────────────────────────────────────────────

Write-Info "Checking resource group: $ResourceGroupName"
$rg = az group exists -n $ResourceGroupName
if ($rg -eq "false") {
    Write-Info "Creating resource group: $ResourceGroupName in $Location"
    az group create -n $ResourceGroupName -l $Location --output none
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create resource group"
    }
    Write-Success "Resource group created"
} else {
    Write-Info "Resource group already exists"
}

# ────────────────────────────────────────────────────────────
# Create Storage Account
# ────────────────────────────────────────────────────────────

Write-Info "Creating storage account: $StorageAccountName"
az storage account create `
    -n $StorageAccountName `
    -g $ResourceGroupName `
    -l $Location `
    --sku Standard_LRS `
    --https-only `
    --output none

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create storage account. The name may already exist. Try another name."
}
Write-Success "Storage account created: $StorageAccountName"

# ────────────────────────────────────────────────────────────
# Create Blob Container
# ────────────────────────────────────────────────────────────

Write-Info "Creating blob container: $ContainerName"
az storage container create `
    -n $ContainerName `
    --account-name $StorageAccountName `
    --output none

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create blob container"
}
Write-Success "Blob container created"

# ────────────────────────────────────────────────────────────
# Get Storage Account Connection String
# ────────────────────────────────────────────────────────────

$storageKey = az storage account keys list -g $ResourceGroupName -n $StorageAccountName --query '[0].value' -o tsv
Write-Success "Storage account key retrieved"

# ────────────────────────────────────────────────────────────
# Display Configuration
# ────────────────────────────────────────────────────────────

Write-Info ""
Write-Info "════════════════════════════════════════════════════════════"
Write-Info "Backend Configuration Created Successfully!"
Write-Info "════════════════════════════════════════════════════════════"
Write-Info ""
Write-Info "Add this to your providers.tf (uncomment the backend block):"
Write-Info ""
Write-Host @"
terraform {
  backend "azurerm" {
    resource_group_name  = "$ResourceGroupName"
    storage_account_name = "$StorageAccountName"
    container_name       = "$ContainerName"
    key                  = "doclynk.terraform.tfstate"
  }
}
"@ -ForegroundColor Cyan

Write-Info ""
Write-Warn "Next steps:"
Write-Info "  1. Update the backend block in providers.tf"
Write-Info "  2. Run: terraform init"
Write-Info "  3. Answer 'yes' when prompted to copy state to remote backend"
Write-Info ""
Write-Warn "Storage account details (for reference):"
Write-Info "  Resource Group: $ResourceGroupName"
Write-Info "  Storage Account: $StorageAccountName"
Write-Info "  Container: $ContainerName"
Write-Info "  Location: $Location"
Write-Info ""
