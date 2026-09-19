terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.130"
    }
    local  = { source = "hashicorp/local", version = "~> 2.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
    tls    = { source = "hashicorp/tls", version = "~> 4.0" }
  }
}

provider "aws" {
  region = var.awslogs_region
}

provider "databricks" {

}
