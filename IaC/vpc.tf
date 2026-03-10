module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.21"

  name = "${local.name_prefix}-vpc"
  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.available.names, 0, length(var.private_subnet_cidrs))
  public_subnets  = var.public_subnet_cidrs
  private_subnets = var.private_subnet_cidrs

  enable_dns_hostnames = true
  enable_dns_support   = true

  # Sem NAT Gateway — subnets privadas sem acesso à internet é intencional
  enable_nat_gateway = false
  single_nat_gateway = false

  # ECS controla IP público via assign_public_ip = true no serviço
  map_public_ip_on_launch = false

  public_subnet_names  = ["${local.name_prefix}-public-1"]
  private_subnet_names = [for i, _ in var.private_subnet_cidrs : "${local.name_prefix}-private-${i + 1}"]

  tags                     = local.common_tags
  vpc_tags                 = { Name = "${local.name_prefix}-vpc" }
  igw_tags                 = { Name = "${local.name_prefix}-igw" }
  public_route_table_tags  = { Name = "${local.name_prefix}-rt-public" }
  private_route_table_tags = { Name = "${local.name_prefix}-rt-private" }
}

# S3 Gateway Endpoint — recurso standalone (módulo v5 removeu suporte inline)
# Lambda (private) e ECS (public) acessam S3 sem custo de transferência
# resource "aws_vpc_endpoint" "s3" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.awslogs_region}.s3"
#   vpc_endpoint_type = "Gateway"

#   route_table_ids = concat(
#     module.vpc.public_route_table_ids,
#     module.vpc.private_route_table_ids
#   )

#   tags = merge(local.common_tags, { Name = "${local.name_prefix}-vpce-s3" })
# }
