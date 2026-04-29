# ──────────────────────────────────────────────────────────────
# DocLynk Azure – Staging Environment Terraform Variables
# ──────────────────────────────────────────────────────────────
# 
# Usage:
#   terraform plan -var-file=staging.tfvars
#   terraform apply -var-file=staging.tfvars
#
# IMPORTANT:
#   1. Generate secrets using:
#      - JWT/OTP secrets: openssl rand -hex 32
#      - Passwords: Use a password manager (different from dev/prod)
#   2. Get Resend API key from: https://resend.com/api-keys
#   3. Use Standard tier ACR and S1 App Service plan
#   4. Enable monitoring for testing observability
# ──────────────────────────────────────────────────────────────

# ── Azure Subscription ──────────────────────────────────────
subscription_id = "47bc037a-7fb4-43d0-b1a5-2cf5be815f20"

# ── General ─────────────────────────────────────────────────
project_name        = "doclynk"
location            = "centralindia"
environment         = "staging"
resource_group_name = "doclynk-staging-rg"

# ── MySQL ───────────────────────────────────────────────────
mysql_server_name    = "doclynk-db-staging"
mysql_location       = "southeastasia"
mysql_admin_username = "docadmin"
# SENSITIVE: Provide via command line or environment
# mysql_admin_password = "Staging@Secure2024!"
mysql_database_name         = "doclynk_staging"
mysql_sku_name              = "B_Standard_B2s" # More resources than dev
mysql_version               = "8.0.21"
mysql_storage_gb            = 50
mysql_backup_retention_days = 14

# ── Container Registry ──────────────────────────────────────
acr_name = "doclynkregistrystaging"
acr_sku  = "Standard" # Standard for staging

# ── App Service (Backend) ───────────────────────────────────
app_service_plan_name = "ASP-doclynk-staging"
app_service_sku       = "S1" # Standard tier for staging
backend_app_name      = "doclynk-backend-staging"

# ── Static Web App (Frontend) ───────────────────────────────
static_web_app_name     = "doclynk-frontend-staging"
static_web_app_sku_tier = "Standard"
static_web_app_sku_size = "Standard"
static_web_app_location = "eastasia"

# ── Application Secrets ─────────────────────────────────────
# Generate using: openssl rand -hex 32
# SENSITIVE: Provide via command line or environment
# jwt_secret_key = "xxxxxxxx..."
jwt_algorithm               = "HS256"
access_token_expire_minutes = 60
# otp_expire_minutes = 10 (uses default)
# otp_max_attempts = 5 (uses default)
# otp_secret_key = "xxxxxxxx..." (SENSITIVE)
# resend_api_key = "re_xxxxx..." (SENSITIVE)
resend_from_email = "noreply+staging@doclynk.nithilan.tech"

# ── CORS (leave empty to auto-generate from SWA + localhost) ─
frontend_origins = ""

# ── Monitoring (enabled for staging) ─────────────────────────
enable_monitoring  = true
grafana_sku        = "Standard"
log_retention_days = 30
