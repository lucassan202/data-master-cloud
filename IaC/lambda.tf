# ---------------------------------------------------------------------------
# Variáveis para a Lambda
# ---------------------------------------------------------------------------
variable "lambda_function_name" {
  description = "Nome da função Lambda"
  type        = string
  default     = "download-csv-consumer"
}

variable "lambda_timeout" {
  description = "Timeout da Lambda em segundos"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Memória da Lambda em MB"
  type        = number
  default     = 512
}

variable "lambda_role_arn" {
  description = "ARN da IAM Role existente para execução da Lambda"
  type        = string
  default     = "arn:aws:iam::120945137272:role/lambda_execution_role"
}

# ---------------------------------------------------------------------------
# Data source para buscar o objeto S3 (para o source_code_hash)
# ---------------------------------------------------------------------------
# data "aws_s3_object" "lambda_zip" {
#   bucket = "${var.environment}-us-east-2-data-master"
#   key    = "tmp/lambda_function.zip"
# }

# ---------------------------------------------------------------------------
# Lambda Function
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "download_csv_lambda" {
  function_name    = var.lambda_function_name
  role            = var.lambda_role_arn
  handler         = "lambda_download_csv.lambda_handler"
  s3_bucket        = "${var.environment}-us-east-2-data-master"
  s3_key           = "lambda_function.zip"
  source_code_hash = filebase64sha256("tmp/lambda_function.zip")

  runtime = "python3.11"
  timeout = var.lambda_timeout
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
}

# Output URLs da Lambda
output "lambda_function_arn" {
  value = aws_lambda_function.download_csv_lambda.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.download_csv_lambda.function_name
}

output "lambda_invoke_arn" {
  value = aws_lambda_function.download_csv_lambda.invoke_arn
}
