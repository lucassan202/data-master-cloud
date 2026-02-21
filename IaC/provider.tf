terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
    aws = {
      source  = "hashicorp/aws"
    }
  }
}

provider "aws" {  
  region = "us-east-2"
}