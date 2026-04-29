# ──────────────────────────────────────────────────────────────
# DocLynk Azure – Outputs
# ──────────────────────────────────────────────────────────────

# ── Resource Group ───────────────────────────────────────────

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Azure region"
  value       = azurerm_resource_group.main.location
}

# ── MySQL ────────────────────────────────────────────────────

output "mysql_fqdn" {
  description = "MySQL Flexible Server fully-qualified domain name"
  value       = azurerm_mysql_flexible_server.main.fqdn
}

output "mysql_database_name" {
  description = "Application database name"
  value       = azurerm_mysql_flexible_database.app.name
}

output "mysql_admin_username" {
  description = "MySQL admin login"
  value       = azurerm_mysql_flexible_server.main.administrator_login
}

# ── Container Registry ──────────────────────────────────────

output "acr_login_server" {
  description = "ACR login server URL"
  value       = azurerm_container_registry.main.login_server
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.main.admin_username
}

output "acr_admin_password" {
  description = "ACR admin password"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

# ── Backend App Service ─────────────────────────────────────

output "backend_url" {
  description = "Backend App Service URL"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "backend_app_name" {
  description = "Backend Web App name (for az webapp commands)"
  value       = azurerm_linux_web_app.backend.name
}

# ── Frontend Static Web App ─────────────────────────────────

output "frontend_url" {
  description = "Frontend Static Web App URL"
  value       = local.frontend_public_url
}

output "frontend_api_token" {
  description = "SWA deployment token (use as AZURE_STATIC_WEB_APPS_API_TOKEN in CI)"
  value       = azurerm_static_web_app.frontend.api_key
  sensitive   = true
}

# ── Monitoring (conditional) ─────────────────────────────────

output "grafana_url" {
  description = "Azure Managed Grafana dashboard URL"
  value       = var.enable_monitoring ? azurerm_dashboard_grafana.main[0].endpoint : ""
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID (empty if monitoring disabled)"
  value       = var.enable_monitoring ? azurerm_log_analytics_workspace.main[0].id : ""
}

