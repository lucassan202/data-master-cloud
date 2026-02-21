terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
    aws = {
      region = "us-east-2"
    }
  }
}
