# ---------------------------------------------------------------------------
# Projeto / Ambiente
# ---------------------------------------------------------------------------
variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "env" {
  description = "Ambiente de execução (dev | pro)"
  type        = string
}

variable "environment" {
  description = "Tipo de Ambiente (dev | pro)"
  type        = string
}

variable "environment_key" {
  description = "Chave do ambiente"
  type        = string
}

variable "environment_version" {
  description = "Versão do ambiente"
  type        = string
}

variable "awslogs_region" {
  description = "Região AWS para logs e recursos"
  type        = string
}

# ---------------------------------------------------------------------------
# Rede / VPC
# ---------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block da VPC"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "Lista de CIDRs das subnets públicas"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "Lista de CIDRs das subnets privadas"
  type        = list(string)
}

# ---------------------------------------------------------------------------
# Cloud Map / Service Discovery
# ---------------------------------------------------------------------------
variable "cloudmap_namespace_name" {
  description = "Nome do namespace DNS privado do Cloud Map"
  type        = string
}

# ---------------------------------------------------------------------------
# ECS / Container
# ---------------------------------------------------------------------------
variable "docker_image_name" {
  description = "Imagem Docker do container Selenium"
  type        = string
}

variable "container_port" {
  description = "Porta exposta pelo container"
  type        = number
}

variable "cpu" {
  description = "CPU units da task ECS"
  type        = number
}

variable "memory" {
  description = "Memória em MB da task ECS"
  type        = number
}

variable "s3_env_vars_file_arn" {
  description = "ARN do arquivo vars.env no S3 para injeção de variáveis no ECS"
  type        = string
}

variable "health_check_path" {
  description = "Path do health check HTTP"
  type        = string
  default     = "/"
}

variable "lambda_timeout" {
  description = "Timeout das funções Lambda em segundos"
  type        = number
  default     = 300
}

variable "lambda_memory_mb" {
  description = "Memória da Lambda screp em MB"
  type        = number
}

# ---------------------------------------------------------------------------
# Lambda — download-csv-consumer
# ---------------------------------------------------------------------------
variable "lambda_function_name" {
  description = "Nome da função Lambda"
  type        = string
  default     = "download-csv-consumer"
}

variable "lambda_memory_size" {
  description = "Memória da Lambda download-csv em MB"
  type        = number
  default     = 512
}

# ---------------------------------------------------------------------------
# Databricks — Notebooks
# ---------------------------------------------------------------------------
variable "notebook_subdirectory" {
  description = "Nome para diretório onde armazenar o notebook."
  type        = string
  default     = "Consumidor"
}

variable "notebook_language" {
  description = "Linguagem de programação do notebook."
  type        = string
}

variable "warehouse_name" {
  description = "Nome (ou parte do nome) do SQL Warehouse existente no Databricks."
  type        = string
}

# ---------------------------------------------------------------------------
# Databricks — Jobs
# ---------------------------------------------------------------------------
variable "datrefcarga" {
  description = "Data de referência para carga no formato string."
  type        = string
}

variable "notification_emails" {
  description = "Lista de e-mails para notificação de falha no Databricks e Airflow"
  type        = list(string)
  default     = ["lucas_san20@hotmail.com"]
}

variable "databricks_grant_principal" {
  description = "Usuário ou grupo Databricks que receberá os GRANTs nas tabelas"
  type        = string
  default     = "lucas_san20@hotmail.com"
}

variable "airflow_admin_username" {
  description = "Usuário administrador do Airflow"
  type        = string
  default     = "admin"
}

variable "airflow_admin_password" {
  description = "Senha do administrador do Airflow"
  type        = string
  sensitive   = true
  default     = null
}

variable "airflow_admin_email" {
  description = "E-mail do administrador do Airflow"
  type        = string
  default     = "admin@example.com"
}

variable "airflow_ssh_cidr_blocks" {
  description = "CIDRs autorizados a acessar SSH e a UI do Airflow"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
