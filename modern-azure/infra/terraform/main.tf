# ──────────────────────────────────────────────────────────────
# DocLynk Azure – Main Infrastructure
# ──────────────────────────────────────────────────────────────

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  # Build the backend public URL from the app name
  backend_url = "https://${var.backend_app_name}.azurewebsites.net"

  # CORS: merge user-supplied origins with the public frontend URL
  frontend_public_url = "https://doclynk-frontend-docker.azurewebsites.net"
  frontend_origins = var.frontend_origins != "" ? var.frontend_origins : join(",", [
    local.frontend_public_url,
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
  ])
}

# ─────────────────────────────────────────────────────────────
# 1. Resource Group
# ─────────────────────────────────────────────────────────────

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# ─────────────────────────────────────────────────────────────
# 2. Azure Database for MySQL – Flexible Server
# ─────────────────────────────────────────────────────────────

resource "azurerm_mysql_flexible_server" "main" {
  name                   = var.mysql_server_name
  resource_group_name    = azurerm_resource_group.main.name
  location               = var.mysql_location
  administrator_login    = var.mysql_admin_username
  administrator_password = var.mysql_admin_password
  sku_name               = var.mysql_sku_name
  version                = var.mysql_version
  zone                   = "1"

  storage {
    size_gb = var.mysql_storage_gb
  }

  backup_retention_days = var.mysql_backup_retention_days

  tags = local.common_tags
}

# Enforce SSL on all connections
resource "azurerm_mysql_flexible_server_configuration" "require_ssl" {
  name                = "require_secure_transport"
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_mysql_flexible_server.main.name
  value               = "ON"
}

# Allow Azure services to connect (needed by App Service)
resource "azurerm_mysql_flexible_server_firewall_rule" "allow_azure" {
  name                = "AllowAzureServices"
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_mysql_flexible_server.main.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
}

# Allow local development access (optional – set your IP)
resource "azurerm_mysql_flexible_server_firewall_rule" "allow_local_dev" {
  name                = "AllowLocalDev"
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_mysql_flexible_server.main.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "255.255.255.255"
}

# Application database
resource "azurerm_mysql_flexible_database" "app" {
  name                = var.mysql_database_name
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_mysql_flexible_server.main.name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
}

# ─────────────────────────────────────────────────────────────
# 3. Azure Container Registry
# ─────────────────────────────────────────────────────────────

resource "azurerm_container_registry" "main" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
  admin_enabled       = true

  tags = local.common_tags
}

# ─────────────────────────────────────────────────────────────
# 4. App Service – Backend (Linux Container)
# ─────────────────────────────────────────────────────────────

resource "azurerm_service_plan" "backend" {
  name                = var.app_service_plan_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.app_service_sku

  tags = local.common_tags
}

resource "azurerm_linux_web_app" "backend" {
  name                = var.backend_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.backend.id
  https_only          = true

  site_config {
    always_on = true

    application_stack {
      python_version = "3.11"
    }

    app_command_line                  = "uvicorn app.main:app --host 0.0.0.0 --port 8000"
    health_check_path                 = "/health"
    health_check_eviction_time_in_min = 5
  }

  app_settings = {
    # ── Database ────────────────────────────────────────────
    DB_HOST     = azurerm_mysql_flexible_server.main.fqdn
    DB_NAME     = azurerm_mysql_flexible_database.app.name
    DB_USER     = var.mysql_admin_username
    DB_PASSWORD = var.mysql_admin_password
    DB_PORT     = "3306"
    DB_SSL_MODE = "require"

    # ── Auth / OTP ──────────────────────────────────────────
    JWT_SECRET_KEY              = var.jwt_secret_key
    JWT_ALGORITHM               = var.jwt_algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = tostring(var.access_token_expire_minutes)
    OTP_EXPIRE_MINUTES          = tostring(var.otp_expire_minutes)
    OTP_MAX_ATTEMPTS            = tostring(var.otp_max_attempts)
    OTP_SECRET_KEY              = var.otp_secret_key

    # ── CORS ────────────────────────────────────────────────
    FRONTEND_ORIGINS    = local.frontend_origins
    FRONTEND_PUBLIC_URL = local.frontend_public_url

    # ── Email ───────────────────────────────────────────────
    RESEND_API_KEY    = var.resend_api_key
    RESEND_FROM_EMAIL = var.resend_from_email

    # ── Platform ──────────────────────────────────────────
    SCM_DO_BUILD_DURING_DEPLOYMENT      = "true"
    WEBSITES_PORT                        = "8000"
  }

  tags = local.common_tags
}

# ─────────────────────────────────────────────────────────────
# 5. Azure Static Web App – Frontend
# ─────────────────────────────────────────────────────────────

resource "azurerm_static_web_app" "frontend" {
  name                = var.static_web_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = var.static_web_app_location
  sku_tier            = var.static_web_app_sku_tier
  sku_size            = var.static_web_app_sku_size

  tags = local.common_tags
}

# ─────────────────────────────────────────────────────────────
# 6. Monitoring – Log Analytics + Azure Managed Grafana
# ─────────────────────────────────────────────────────────────

# Current Azure user (needed for Grafana admin role assignment)
data "azurerm_client_config" "current" {}

# Log Analytics Workspace – central log sink for all diagnostics
resource "azurerm_log_analytics_workspace" "main" {
  count               = var.enable_monitoring ? 1 : 0
  name                = "${var.project_name}-logs"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = local.common_tags
}

# Azure Managed Grafana
resource "azurerm_dashboard_grafana" "main" {
  count                             = var.enable_monitoring ? 1 : 0
  name                              = "${var.project_name}-grafana"
  resource_group_name               = azurerm_resource_group.main.name
  location                          = azurerm_resource_group.main.location
  grafana_major_version             = 11
  api_key_enabled                   = true
  deterministic_outbound_ip_enabled = false
  public_network_access_enabled     = true
  sku                               = var.grafana_sku
  zone_redundancy_enabled           = false

  identity {
    type = "SystemAssigned"
  }

  azure_monitor_workspace_integrations {
    resource_id = azurerm_monitor_workspace.main[0].id
  }

  tags = local.common_tags
}

# Azure Monitor Workspace (Prometheus-compatible metrics store)
resource "azurerm_monitor_workspace" "main" {
  count               = var.enable_monitoring ? 1 : 0
  name                = "${var.project_name}-monitor"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  tags = local.common_tags
}

# ── Role Assignments ─────────────────────────────────────────

# Grant Grafana "Monitoring Reader" on the subscription so it can
# read Azure Monitor metrics from all resources
resource "azurerm_role_assignment" "grafana_monitoring_reader" {
  count                = var.enable_monitoring ? 1 : 0
  scope                = "/subscriptions/${var.subscription_id}"
  role_definition_name = "Monitoring Reader"
  principal_id         = azurerm_dashboard_grafana.main[0].identity[0].principal_id
}

# Grant Grafana "Log Analytics Reader" on the workspace
resource "azurerm_role_assignment" "grafana_log_analytics_reader" {
  count                = var.enable_monitoring ? 1 : 0
  scope                = azurerm_log_analytics_workspace.main[0].id
  role_definition_name = "Log Analytics Reader"
  principal_id         = azurerm_dashboard_grafana.main[0].identity[0].principal_id
}

# Grant the current user "Grafana Admin" so you can access dashboards
resource "azurerm_role_assignment" "grafana_admin" {
  count                = var.enable_monitoring ? 1 : 0
  scope                = azurerm_dashboard_grafana.main[0].id
  role_definition_name = "Grafana Admin"
  principal_id         = data.azurerm_client_config.current.object_id
}

# ── Diagnostic Settings (pipe logs & metrics into Log Analytics) ──

# Backend App Service → Log Analytics
resource "azurerm_monitor_diagnostic_setting" "backend" {
  count                      = var.enable_monitoring ? 1 : 0
  name                       = "${var.project_name}-backend-diag"
  target_resource_id         = azurerm_linux_web_app.backend.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main[0].id

  enabled_log {
    category = "AppServiceHTTPLogs"
  }

  enabled_log {
    category = "AppServiceConsoleLogs"
  }

  enabled_log {
    category = "AppServiceAppLogs"
  }

  enabled_log {
    category = "AppServicePlatformLogs"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}

# MySQL Flexible Server → Log Analytics
resource "azurerm_monitor_diagnostic_setting" "mysql" {
  count                      = var.enable_monitoring ? 1 : 0
  name                       = "${var.project_name}-mysql-diag"
  target_resource_id         = azurerm_mysql_flexible_server.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main[0].id

  enabled_log {
    category = "MySqlSlowLogs"
  }

  enabled_log {
    category = "MySqlAuditLogs"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}
