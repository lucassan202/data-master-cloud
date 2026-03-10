resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

resource "aws_cloudwatch_log_group" "ecs_selenium" {
  name              = "/ecs/${local.name_prefix}-selenium"
  retention_in_days = 7

  tags = local.common_tags
}

resource "aws_ecs_task_definition" "selenium" {
  family                   = "${local.name_prefix}-selenium"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_execution_role_arn

  container_definitions = jsonencode([
    {
      name  = "selenium"
      image = var.docker_image_name

      portMappings = [
        {
          containerPort = tonumber(var.container_port)
          protocol      = "tcp"
          name          = "selenium"
        }
      ]

      # Carrega variáveis de ambiente do arquivo vars.env no S3
      environmentFiles = [
        {
          value = var.s3_env_vars_file_arn
          type  = "s3"
        }
      ]

      # Selenium standalone expõe /status quando pronto
      healthCheck = {
        command     = ["CMD-SHELL", "curl -sf http://localhost:4444/status | grep -q '\"ready\":true' || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_selenium.name
          "awslogs-region"        = var.awslogs_region
          "awslogs-stream-prefix" = "selenium"
        }
      }

      essential = true
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_service" "selenium" {
  name            = "${local.name_prefix}-selenium-svc"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.selenium.arn
  desired_count   = 0
  launch_type     = "FARGATE"

  # Impede que o Terraform reset o desired_count quando o Airflow o alterar
  lifecycle {
    ignore_changes = [desired_count]
  }

  network_configuration {
    subnets          = [module.vpc.public_subnets[0]]
    security_groups  = [module.ecs_selenium_sg.security_group_id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.selenium.arn
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  tags = local.common_tags
}
