# ──────────────────────────────────────────────────────────────
# DocLynk Azure – Terraform Provider Configuration
# ──────────────────────────────────────────────────────────────
#
# This file configures:
#   1. Terraform version requirements
#   2. Required Azure provider
#   3. State management (local or remote)
#   4. Azure provider configuration
#
# Documentation:
#   - Terraform: https://www.terraform.io/language/settings
#   - Azure Provider: https://registry.terraform.io/providers/hashicorp/azurerm
#   - Backend State: See ./BACKEND_SETUP.md
# ──────────────────────────────────────────────────────────────

terraform {
  # ── Terraform Version ──────────────────────────────────────
  # Minimum Terraform version required for this configuration
  required_version = ">= 1.5"

  # ── Required Providers ─────────────────────────────────────
  # Specify provider requirements and versions
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0" # Allows 4.x.x, but not 5.x.x
    }
  }

  # ── State Management ───────────────────────────────────────
  # Local State (Default for Development)
  #   - State stored in ./terraform.tfstate
  #   - Simple, but not suitable for teams
  #   - .gitignore excludes from version control
  #
  # Remote State (Recommended for Production)
  #   - State stored in Azure Storage Account
  #   - Enables team collaboration with state locking
  #   - Automatic backups and encryption
  #
  # Setup Instructions:
  #   1. Run: .\setup-backend.ps1
  #   2. Uncomment the backend block below
  #   3. Update with your storage account details
  #   4. Run: terraform init
  #   5. Answer 'yes' when prompted to copy state
  #
  # See BACKEND_SETUP.md for detailed instructions

  # ── REMOTE STATE (Uncomment for Production) ────────────────
  # backend "azurerm" {
  #   resource_group_name  = "doclynk-tfstate-rg"
  #   storage_account_name = "doclynktfstate"
  #   container_name       = "tfstate"
  #   key                  = "doclynk.terraform.tfstate"
  # }
}

# ──────────────────────────────────────────────────────────────
# Azure Provider Configuration
# ──────────────────────────────────────────────────────────────

provider "azurerm" {
  # ── Features ───────────────────────────────────────────────
  # Configure provider-level behaviors
  # See: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/features-block
  features {}

  # ── Subscription ID ────────────────────────────────────────
  # Specifies which Azure subscription to use
  # Can also be set via environment variable: ARM_SUBSCRIPTION_ID
  subscription_id = var.subscription_id
}

# ──────────────────────────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────────────────────────
#
# Terraform uses Azure CLI authentication by default.
# The provider will use credentials from:
#   1. ARM_CLIENT_ID, ARM_CLIENT_SECRET, ARM_TENANT_ID (Service Principal)
#   2. az account show (Azure CLI)
#   3. Azure managed identity (when running in Azure)
#
# Verify authentication:
#   az account show
#   az account set --subscription <subscription-id>
# ──────────────────────────────────────────────────────────────
