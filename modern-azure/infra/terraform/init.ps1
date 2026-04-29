# Initialize Terraform for DocLynk Azure Project
# This script performs initial setup for Terraform deployment

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev",

    [Parameter(Mandatory = $false)]
    [switch]$SkipValidation,

    [Parameter(Mandatory = $false)]
    [switch]$RemoteState
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
# 1. Prerequisites Check
# ────────────────────────────────────────────────────────────

Write-Info "Checking prerequisites..."

# Check Terraform
$tfVersion = terraform --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Terraform not found. Please install Terraform from https://www.terraform.io/downloads.html"
}
Write-Success "Terraform found: $(($tfVersion | Select-Object -First 1).Split()[1])"

# Check Azure CLI
$ErrorActionPreference = "Continue"
$azCheck = az --version 2>&1 | Out-String
$ErrorActionPreference = "Stop"

if ($azCheck -notmatch "azure-cli") {
    Write-Error "Azure CLI not found. Please install from https://learn.microsoft.com/cli/azure/install-azure-cli"
}
$azVersionLine = $azCheck.Split([System.Environment]::NewLine) | Where-Object { $_ -match "azure-cli" } | Select-Object -First 1
Write-Success "Azure CLI found: $azVersionLine"

# Check Azure authentication
$currentAz = az account show --query name -o tsv 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Not authenticated to Azure. Running 'az login'..."
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Azure login failed"
    }
}
Write-Success "Authenticated as: $currentAz"

# ────────────────────────────────────────────────────────────
# 2. Navigate to Terraform directory
# ────────────────────────────────────────────────────────────

$tfDir = (Get-Item $PSScriptRoot).FullName
if (-not (Test-Path "$tfDir\main.tf")) {
    Write-Error "main.tf not found in $tfDir. Please run this script from the Terraform directory."
}

Write-Info "Working directory: $tfDir"
Push-Location $tfDir

# ────────────────────────────────────────────────────────────
# 3. Setup Variables
# ────────────────────────────────────────────────────────────

Write-Info "Setting up environment: $Environment"

$tfvarsFile = "$Environment.tfvars"
if (-not (Test-Path $tfvarsFile)) {
    Write-Error "$tfvarsFile not found. Please create it from the example: Copy-Item terraform.tfvars.example $tfvarsFile"
}

Write-Success "Using variables file: $tfvarsFile"

# Check for sensitive values
Write-Warn "Note: Sensitive values must be provided via environment variables or command line"
Write-Info "  Set environment variables for secrets:"
Write-Info "    `$env:TF_VAR_mysql_admin_password = 'your_password'"
Write-Info "    `$env:TF_VAR_jwt_secret_key = 'your_key'"
Write-Info "    `$env:TF_VAR_otp_secret_key = 'your_key'"
Write-Info "    `$env:TF_VAR_resend_api_key = 'your_key'"

# ────────────────────────────────────────────────────────────
# 4. Terraform Init
# ────────────────────────────────────────────────────────────

Write-Info "Initializing Terraform..."
terraform init -no-color
if ($LASTEXITCODE -ne 0) {
    Write-Error "Terraform init failed"
}
Write-Success "Terraform initialized successfully"

# ────────────────────────────────────────────────────────────
# 5. Terraform Validate
# ────────────────────────────────────────────────────────────

if (-not $SkipValidation) {
    Write-Info "Validating Terraform configuration..."
    terraform validate -no-color
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Terraform validation failed"
    }
    Write-Success "Validation passed"
}

# ────────────────────────────────────────────────────────────
# 6. Format check
# ────────────────────────────────────────────────────────────

Write-Info "Checking Terraform formatting..."
$formatCheck = terraform fmt -check -no-color 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Terraform files need formatting. Running terraform fmt..."
    terraform fmt -recursive -no-color
    Write-Success "Files formatted"
} else {
    Write-Success "Formatting looks good"
}

# ────────────────────────────────────────────────────────────
# 7. Plan and display summary
# ────────────────────────────────────────────────────────────

Write-Info "Generating Terraform plan..."
Write-Info "Variables file: $tfvarsFile"
Write-Info "Full path: $(Resolve-Path $tfvarsFile)"
$planFile = "tfplan-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
terraform plan -var-file="$tfvarsFile" -out="$planFile" -no-color
if ($LASTEXITCODE -ne 0) {
    Write-Error "Terraform plan failed"
}

Write-Success "Plan generated: $planFile"
Write-Info ""
Write-Info "Next steps:"
Write-Info "  1. Review the plan: terraform show $planFile"
Write-Info "  2. Apply the plan: terraform apply $planFile"
Write-Info "  3. Or review and apply: terraform apply -var-file=$tfvarsFile"

# ────────────────────────────────────────────────────────────
# Cleanup
# ────────────────────────────────────────────────────────────

Pop-Location
Write-Success "Initialization complete!"
