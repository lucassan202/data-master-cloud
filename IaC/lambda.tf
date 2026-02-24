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

# ---------------------------------------------------------------------------
# IAM Role para a Lambda
# ---------------------------------------------------------------------------
resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda_execution_role_${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWSLambdaBasicExecutionRole policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy para acesso ao S3
resource "aws_iam_policy" "lambda_s3_policy" {
  name = "lambda_s3_policy_${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "arn:aws:s3:::${var.environment}-us-east-2-data-master/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${var.environment}-us-east-2-data-master"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attachment" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

# ---------------------------------------------------------------------------
# Lambda Function
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "download_csv_lambda" {
  filename         = "lambda_function.zip"
  function_name    = var.lambda_function_name
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "lambda_download_csv.lambda_handler"
  source_code_hash = filebase64sha256("lambda_function.zip")

  runtime = "python3.11"
  timeout = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = {
      ENV = var.environment
    }
  }

  # Dependências do Python layer (opcional)
  # layers = [aws_lambda_layer_version.python_dependencies.arn]

  tags = {
    Environment = var.environment
    Project     = "data-master-cloud"
  }
}

# Output URL da Lambda
output "lambda_function_arn" {
  value = aws_lambda_function.download_csv_lambda.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.download_csv_lambda.function_name
}

output "lambda_invoke_arn" {
  value = aws_lambda_function.download_csv_lambda.invoke_arn
}
