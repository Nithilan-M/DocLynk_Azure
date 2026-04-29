# ──────────────────────────────────────────────────────────────
# DocLynk Azure – Development Environment Terraform Variables
# ──────────────────────────────────────────────────────────────
# 
# Usage:
#   terraform plan -var-file=dev.tfvars
#   terraform apply -var-file=dev.tfvars
#
# IMPORTANT:
#   1. Generate secrets using:
#      - JWT/OTP secrets: openssl rand -hex 32
#      - Passwords: Use a password manager
#   2. Get Resend API key from: https://resend.com/api-keys
#   3. Keep this file in version control (no secrets should be here)
#   4. Sensitive values should be provided via environment or command line
# ──────────────────────────────────────────────────────────────

# ── Azure Subscription ──────────────────────────────────────
subscription_id = "47bc037a-7fb4-43d0-b1a5-2cf5be815f20"

# ── General ─────────────────────────────────────────────────
project_name        = "doclynk"
location            = "centralindia"
environment         = "dev"
resource_group_name = "doclynk-dev-rg"

# ── MySQL ───────────────────────────────────────────────────
mysql_server_name    = "doclynk-db-dev"
mysql_location       = "southeastasia"
mysql_admin_username = "docadmin"
# SENSITIVE: Provide via command line or environment
# mysql_admin_password = "Dev@Secure2024!"
mysql_database_name         = "doclynk_dev"
mysql_sku_name              = "B_Standard_B1ms"
mysql_version               = "8.0.21"
mysql_storage_gb            = 20
mysql_backup_retention_days = 7

# ── Container Registry ──────────────────────────────────────
acr_name = "doclynkregistrydev"
acr_sku  = "Basic" # Basic is sufficient for dev

# ── App Service (Backend) ───────────────────────────────────
app_service_plan_name = "ASP-doclynk-dev"
app_service_sku       = "B1" # Burstable tier for dev
backend_app_name      = "doclynk-backend-dev"

# ── Static Web App (Frontend) ───────────────────────────────
static_web_app_name     = "doclynk-frontend-dev"
static_web_app_sku_tier = "Free"
static_web_app_sku_size = "Free"
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
resend_from_email = "noreply+dev@doclynk.nithilan.tech"

# ── CORS (leave empty to auto-generate from SWA + localhost) ─
frontend_origins = ""

# ── Monitoring (disabled for dev to save costs) ──────────────
enable_monitoring = false
