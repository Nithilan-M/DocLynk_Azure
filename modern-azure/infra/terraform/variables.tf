# ──────────────────────────────────────────────────────────────
# DocLynk Azure – Input Variables
# ──────────────────────────────────────────────────────────────

# ── General ──────────────────────────────────────────────────

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "project_name" {
  description = "Short project slug used for naming resources"
  type        = string
  default     = "doclynk"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "centralindia"
}

variable "environment" {
  description = "Deployment environment tag (dev / staging / prod)"
  type        = string
  default     = "prod"
}

# ── Resource Group ───────────────────────────────────────────

variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "doclynk"
}

# ── MySQL Flexible Server ───────────────────────────────────

variable "mysql_server_name" {
  description = "MySQL Flexible Server name (globally unique)"
  type        = string
  default     = "doclynk-db"
}

variable "mysql_location" {
  description = "Azure region for MySQL (may differ from main location)"
  type        = string
  default     = "southeastasia"
}

variable "mysql_admin_username" {
  description = "MySQL administrator login"
  type        = string
  default     = "docadmin"
}

variable "mysql_admin_password" {
  description = "MySQL administrator password"
  type        = string
  sensitive   = true
}

variable "mysql_database_name" {
  description = "Application database name"
  type        = string
  default     = "doclynkdb"
}

variable "mysql_sku_name" {
  description = "MySQL SKU (e.g. B_Standard_B1ms for burstable)"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "mysql_version" {
  description = "MySQL engine version"
  type        = string
  default     = "8.0.21"
}

variable "mysql_storage_gb" {
  description = "Storage allocated to MySQL in GB"
  type        = number
  default     = 20
}

variable "mysql_backup_retention_days" {
  description = "Number of days to retain MySQL backups"
  type        = number
  default     = 7
}

# ── Azure Container Registry ────────────────────────────────

variable "acr_name" {
  description = "Container Registry name (globally unique, alphanumeric only)"
  type        = string
  default     = "doclynkregistry"
}

variable "acr_sku" {
  description = "ACR pricing tier (Basic / Standard / Premium)"
  type        = string
  default     = "Basic"
}

# ── App Service (Backend) ───────────────────────────────────

variable "app_service_plan_name" {
  description = "App Service Plan name"
  type        = string
  default     = "ASP-doclynk-9488"
}

variable "app_service_sku" {
  description = "App Service Plan SKU (B1 / B2 / S1 etc.)"
  type        = string
  default     = "B1"
}

variable "backend_app_name" {
  description = "Backend Web App name (globally unique)"
  type        = string
  default     = "doclynk-backend-docker"
}

# ── Static Web App (Frontend) ───────────────────────────────

variable "static_web_app_name" {
  description = "Azure Static Web App name"
  type        = string
  default     = "doclynk-frontend"
}

variable "static_web_app_sku_tier" {
  description = "Static Web App SKU tier (Free / Standard)"
  type        = string
  default     = "Free"
}

variable "static_web_app_sku_size" {
  description = "Static Web App SKU size (Free / Standard)"
  type        = string
  default     = "Free"
}

variable "static_web_app_location" {
  description = "Region for Static Web App (limited availability: westus2, centralus, eastus2, westeurope, eastasia)"
  type        = string
  default     = "eastasia"
}

# ── Application Secrets ──────────────────────────────────────

variable "jwt_secret_key" {
  description = "JWT signing secret (64-char hex)"
  type        = string
  sensitive   = true
}

variable "jwt_algorithm" {
  description = "JWT algorithm"
  type        = string
  default     = "HS256"
}

variable "access_token_expire_minutes" {
  description = "Access token lifetime in minutes"
  type        = number
  default     = 60
}

variable "otp_expire_minutes" {
  description = "OTP lifetime in minutes"
  type        = number
  default     = 10
}

variable "otp_max_attempts" {
  description = "Maximum OTP verification attempts"
  type        = number
  default     = 5
}

variable "otp_secret_key" {
  description = "OTP HMAC secret"
  type        = string
  sensitive   = true
}

variable "resend_api_key" {
  description = "Resend email provider API key"
  type        = string
  sensitive   = true
}

variable "resend_from_email" {
  description = "Sender address for transactional emails"
  type        = string
  default     = "MediCare <noreply@doclynk.nithilan.tech>"
}

variable "frontend_origins" {
  description = "Comma-separated CORS origins allowed by the backend"
  type        = string
  default     = ""
}

# ── Monitoring (Grafana + Log Analytics) ─────────────────────

variable "enable_monitoring" {
  description = "Whether to provision Azure Managed Grafana, Log Analytics, and diagnostic settings"
  type        = bool
  default     = true
}

variable "grafana_sku" {
  description = "Azure Managed Grafana SKU (Standard or Essential)"
  type        = string
  default     = "Standard"
}

variable "log_retention_days" {
  description = "Number of days to retain logs in Log Analytics"
  type        = number
  default     = 30
}

