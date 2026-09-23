# ---------------------------------------------------------------------------
# Lambda Function
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "download_csv_lambda" {
  function_name = "${var.lambda_function_name}-${var.env}"
  description   = "Scraper dados.mj.gov.br para download do arquivo CSV mensal de reclamações"
  role          = aws_iam_role.lambda_download.arn
  handler       = "lambda_download_csv.lambda_handler"
  s3_bucket     = data.aws_s3_bucket.data.id
  s3_key        = "tmp/lambda_function.zip"

  runtime     = "python3.11"
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = {
      ENV = var.environment
    }
  }

  tags = {
    Environment = var.environment
    Project     = "data-master-cloud"
  }

  # Create/adopt the Terraform-managed group before the Lambda can use it.
  depends_on = [aws_cloudwatch_log_group.lambda_download]
}

resource "aws_cloudwatch_log_group" "lambda_download" {
  name              = "/aws/lambda/${local.lambda_download_function_name}"
  retention_in_days = 14

  tags = local.common_tags
}


resource "aws_lambda_layer_version" "selenium" {
  layer_name          = "${local.name_prefix}-selenium-layer"
  s3_bucket           = data.aws_s3_bucket.data.id
  s3_key              = "tmp/selenium_layer.zip"
  compatible_runtimes = ["python3.11", "python3.12"]
  description         = "Selenium 4.x client para Lambda"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name_prefix}-screp"
  retention_in_days = 14

  tags = local.common_tags
}

resource "aws_lambda_function" "screp" {
  function_name = "${local.name_prefix}-screp"
  description   = "Scraper consumidor.gov.br usando Selenium remoto no ECS"
  role          = aws_iam_role.lambda_screp.arn
  runtime       = "python3.11"
  s3_bucket     = data.aws_s3_bucket.data.id
  s3_key        = "tmp/selenium_layer.zip"
  handler       = "screp_reclamacoes.lambda_handler"

  layers = [aws_lambda_layer_version.selenium.arn]

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_mb

  vpc_config {
    subnet_ids         = module.vpc.private_subnets
    security_group_ids = [module.lambda_sg.security_group_id]
  }

  environment {
    variables = {
      # DNS Cloud Map — resolve para o IP privado do container ECS quando ativo
      SELENIUM_URL = local.selenium_url
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy.lambda_screp,
  ]

  tags = local.common_tags
}
