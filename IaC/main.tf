data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.project_name}-${var.env}"

  # Extrai nome do bucket de vars.env a partir do ARN: arn:aws:s3:::bucket-name/path
  s3_bucket_name = split("/", replace(var.s3_env_vars_file_arn, "arn:aws:s3:::", ""))[0]

  # Bucket de dados conforme padrão do script Python: {env}-{region}-data-master
  data_bucket_name = "${var.env}-${var.awslogs_region}-data-master"

  # DNS Cloud Map que a Lambda usa para alcançar o Selenium
  selenium_dns = "selenium.${var.cloudmap_namespace_name}"
  selenium_url = "http://${local.selenium_dns}:${var.container_port}"

  common_tags = {
    Project     = var.project_name
    Environment = var.env
    ManagedBy   = "Terraform"
  }
}
