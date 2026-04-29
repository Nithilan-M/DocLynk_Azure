# ──────────────────────────────────────────────────────────────
# DocLynk Azure – Production Environment Terraform Variables
# ──────────────────────────────────────────────────────────────
# 
# Usage:
#   terraform plan -var-file=prod.tfvars
#   terraform apply -var-file=prod.tfvars
#
# CRITICAL SECURITY NOTES:
#   1. Generate strong secrets using: openssl rand -hex 32
#   2. Use a password manager for all passwords
#   3. NEVER commit sensitive values to git
#   4. Provide secrets via environment variables or Azure Key Vault
#   5. Use premium tier resources and redundancy
#   6. Enable monitoring and backups
#   7. Require approval for production deployments
# ──────────────────────────────────────────────────────────────

# ── Azure Subscription ──────────────────────────────────────
subscription_id = "47bc037a-7fb4-43d0-b1a5-2cf5be815f20"

# ── General ─────────────────────────────────────────────────
project_name        = "doclynk"
location            = "centralindia"
environment         = "prod"
resource_group_name = "doclynk-prod-rg"

# ── MySQL ───────────────────────────────────────────────────
mysql_server_name    = "doclynk-db-prod"
mysql_location       = "southeastasia"
mysql_admin_username = "docadmin"
# SENSITIVE: Provide via command line or environment
# mysql_admin_password = "Prod@SecureRandomPassword2024!"
mysql_database_name         = "doclynk_prod"
mysql_sku_name              = "B_Standard_B2s" # Consider D_Standard_D2s for production workloads
mysql_version               = "8.0.21"
mysql_storage_gb            = 100 # Generous storage for production
mysql_backup_retention_days = 35  # ~1 month retention

# ── Container Registry ──────────────────────────────────────
acr_name = "doclynkregistryprod"
acr_sku  = "Premium" # Premium for production (includes webhooks, private endpoints)

# ── App Service (Backend) ───────────────────────────────────
app_service_plan_name = "ASP-doclynk-prod"
app_service_sku       = "P1v2" # Premium tier for production
backend_app_name      = "doclynk-backend-docker"

# ── Static Web App (Frontend) ───────────────────────────────
static_web_app_name     = "doclynk-frontend-prod"
static_web_app_sku_tier = "Standard"
static_web_app_sku_size = "Standard"
static_web_app_location = "eastasia"

# ── Application Secrets ─────────────────────────────────────
# Generate using: openssl rand -hex 32 (must be different from staging/dev)
# SENSITIVE: Provide via environment variables, not in this file!
# Example environment variable setup:
#   $env:TF_VAR_jwt_secret_key = "..."
#   $env:TF_VAR_otp_secret_key = "..."
#   $env:TF_VAR_mysql_admin_password = "..."
#   $env:TF_VAR_resend_api_key = "..."
#
# jwt_secret_key = "PROVIDE_VIA_ENVIRONMENT_VARIABLE"
jwt_algorithm               = "HS256"
access_token_expire_minutes = 60
# otp_expire_minutes = 10 (uses default)
# otp_max_attempts = 5 (uses default)
# otp_secret_key = "PROVIDE_VIA_ENVIRONMENT_VARIABLE"
# resend_api_key = "PROVIDE_VIA_ENVIRONMENT_VARIABLE"
resend_from_email = "noreply@doclynk.nithilan.tech"

# ── CORS (explicitly set allowed origins) ─────────────────
# Format: "https://example.com,https://app.example.com"
# Leave empty to auto-generate from SWA
frontend_origins = ""

# ── Monitoring (fully enabled for production) ────────────────
enable_monitoring  = true
grafana_sku        = "Standard" # or "Essential" for cost savings
log_retention_days = 90         # 3 months retention for production
