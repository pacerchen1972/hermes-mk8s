terraform {
  required_version = ">= 1.5.0"

  required_providers {
    ionoscloud = {
      source  = "ionos-cloud/ionoscloud"
      version = "~> 6.5"
    }
  }
}

provider "ionoscloud" {
  # Credentials are read from environment variables:
  #   IONOS_TOKEN         (preferred)
  # or
  #   IONOS_USERNAME + IONOS_PASSWORD
}
