project_name            = "data-master"
env                     = "dev"
container_port          = "4444"
awslogs_region          = "us-east-2"
docker_image_name       = "selenium/standalone-firefox:4.25.0-20241010"
cpu                     = "1024"
memory                  = "2048"
s3_env_vars_file_arn    = "arn:aws:s3:::dsa-lab5-120945137272/vars.env"
health_check_path       = "/"

# Rede
vpc_cidr                = "10.0.0.0/16"
public_subnet_cidrs     = ["10.0.0.0/24"]
private_subnet_cidrs    = ["10.0.1.0/24", "10.0.2.0/24"]

# Cloud Map (Service Discovery DNS privado)
cloudmap_namespace_name = "data-master"

# Lambda
lambda_timeout          = 900
lambda_memory_mb        = 512
# Gerar antes do apply: ver instruções de packaging abaixo
lambda_layer_zip_path    = "../selenium_layer.zip"

# IAM roles existentes
ecs_task_execution_role_arn = "arn:aws:iam::120945137272:role/ecsTaskExecutionRole"
lambda_execution_role_arn   = "arn:aws:iam::120945137272:role/lambda_execution_role"