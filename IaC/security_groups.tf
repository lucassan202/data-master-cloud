# SG da Lambda — sem ingress (Lambda é apenas cliente)
module "lambda_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${local.name_prefix}-sg-lambda"
  description = "Lambda scraper - egress to Selenium ECS and S3"
  vpc_id      = module.vpc.vpc_id

  ingress_with_cidr_blocks = []
  egress_rules              = ["all-all"]

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-sg-lambda" })
}

# SG do ECS Selenium — sem regra 4444 inline (evita referência circular)
module "ecs_selenium_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${local.name_prefix}-sg-ecs-selenium"
  description = "ECS Selenium - ingress 4444 from Lambda, egress HTTPS for scraping"
  vpc_id      = module.vpc.vpc_id

  ingress_with_cidr_blocks = []
  egress_rules              = ["all-all"]

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-sg-ecs-selenium" })
}

# Regras cross-SG separadas para evitar referência circular no Terraform
resource "aws_security_group_rule" "ecs_ingress_from_lambda" {
  description              = "Selenium WebDriver da Lambda"
  type                     = "ingress"
  from_port                = tonumber(var.container_port)
  to_port                  = tonumber(var.container_port)
  protocol                 = "tcp"
  security_group_id        = module.ecs_selenium_sg.security_group_id
  source_security_group_id = module.lambda_sg.security_group_id
}

resource "aws_security_group_rule" "lambda_egress_to_ecs" {
  description              = "Selenium WebDriver para ECS"
  type                     = "egress"
  from_port                = tonumber(var.container_port)
  to_port                  = tonumber(var.container_port)
  protocol                 = "tcp"
  security_group_id        = module.lambda_sg.security_group_id
  source_security_group_id = module.ecs_selenium_sg.security_group_id
}
