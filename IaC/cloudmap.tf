# Namespace DNS privado — cria zona Route 53 privada associada à VPC
# Ex: dsa-env.local
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = var.cloudmap_namespace_name
  description = "DNS privado para service discovery de ${local.name_prefix}"
  vpc         = module.vpc.vpc_id

  tags = local.common_tags
}

# Service Discovery do Selenium
# DNS resultante: selenium.dsa-env.local → IP privado do container ECS
# TTL=10s para que a Lambda descubra rapidamente o novo IP após o Airflow iniciar o task
resource "aws_service_discovery_service" "selenium" {
  name = "selenium"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      type = "A"
      ttl  = 10
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {}

  tags = local.common_tags
}
