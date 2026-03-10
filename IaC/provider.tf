terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

provider "aws" {
  region = var.awslogs_region
}

provider "databricks" {

}

