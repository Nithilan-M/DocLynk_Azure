# Deploy DocLynk Infrastructure via Terraform
# This script handles planning and applying Terraform changes

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("plan", "apply", "destroy")]
    [string]$Action = "plan",

    [Parameter(Mandatory = $false)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev",

    [Parameter(Mandatory = $false)]
    [switch]$AutoApprove
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
# Preparation
# ────────────────────────────────────────────────────────────

$tfDir = (Get-Item $PSScriptRoot).FullName
if (-not (Test-Path "$tfDir\main.tf")) {
    Write-Error "Not in Terraform directory"
}

Push-Location $tfDir

$tfvarsFile = "$Environment.tfvars"
if (-not (Test-Path $tfvarsFile)) {
    Write-Error "$tfvarsFile not found"
}

Write-Info "Action: $Action"
Write-Info "Environment: $Environment"
Write-Info "Variables: $tfvarsFile"
Write-Info ""

# ────────────────────────────────────────────────────────────
# Validate Configuration
# ────────────────────────────────────────────────────────────

Write-Info "Validating Terraform configuration..."
terraform validate -no-color
if ($LASTEXITCODE -ne 0) {
    Write-Error "Validation failed"
}
Write-Success "Validation passed"
Write-Info ""

# ────────────────────────────────────────────────────────────
# Plan
# ────────────────────────────────────────────────────────────

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$planFile = "tfplan-$Environment-$timestamp"

Write-Info "Generating Terraform plan ($planFile)..."
terraform plan -var-file="$tfvarsFile" -out="$planFile" -no-color
if ($LASTEXITCODE -ne 0) {
    Write-Error "Plan generation failed"
}
Write-Success "Plan generated"
Write-Info ""

# ────────────────────────────────────────────────────────────
# Apply or Destroy
# ────────────────────────────────────────────────────────────

if ($Action -eq "plan") {
    Write-Info "Plan saved: $planFile"
    Write-Info "To apply: terraform apply $planFile"
    Write-Success "Plan only (no changes applied)"
}
elseif ($Action -eq "apply") {
    Write-Warn "APPLYING CHANGES TO $([string]::ToUpper($Environment)) ENVIRONMENT"
    Write-Info ""

    if (-not $AutoApprove) {
        Write-Host "Type 'yes' to confirm: " -ForegroundColor Yellow -NoNewline
        $confirm = Read-Host
        if ($confirm -ne "yes") {
            Write-Info "Cancelled"
            exit 0
        }
    }

    Write-Info "Applying Terraform plan..."
    terraform apply $planFile -no-color
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Apply failed"
    }

    Write-Success "Infrastructure deployed successfully!"
    Write-Info ""
    Write-Info "Deployment outputs:"
    terraform output
}
elseif ($Action -eq "destroy") {
    Write-Warn "⚠️  DESTROYING ALL INFRASTRUCTURE IN $([string]::ToUpper($Environment)) ENVIRONMENT ⚠️"
    Write-Info "This action cannot be undone!"
    Write-Info ""

    if (-not $AutoApprove) {
        $confirmCount = 0
        for ($i = 0; $i -lt 3; $i++) {
            Write-Host "Type 'destroy' to confirm (attempt $($i+1)/3): " -ForegroundColor Red -NoNewline
            $confirm = Read-Host
            if ($confirm -eq "destroy") {
                $confirmCount++
                break
            }
        }

        if ($confirmCount -eq 0) {
            Write-Info "Destruction cancelled"
            exit 0
        }
    }

    Write-Info "Creating destroy plan..."
    terraform plan -destroy -var-file="$tfvarsFile" -out="destroy-$timestamp" -no-color
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Destroy plan failed"
    }

    Write-Info "Executing destroy..."
    terraform apply "destroy-$timestamp" -no-color
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Destroy failed"
    }

    Write-Success "Infrastructure destroyed"
}

# ────────────────────────────────────────────────────────────
# Cleanup
# ────────────────────────────────────────────────────────────

Pop-Location
Write-Success "Operation completed!"
