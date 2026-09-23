locals {
  airflow_enabled   = var.env == "pro"
  airflow_count     = local.airflow_enabled ? 1 : 0
  airflow_bucket    = local.data_bucket_name
  airflow_dags_path = "s3://${local.airflow_bucket}/dags"
}

data "aws_ami" "airflow_ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "tls_private_key" "airflow" {
  count     = local.airflow_count
  algorithm = "RSA"
  rsa_bits  = 4096
}
resource "aws_key_pair" "airflow" {
  count      = local.airflow_count
  key_name   = "${local.name_prefix}-airflow-key"
  public_key = tls_private_key.airflow[0].public_key_openssh
  tags       = merge(local.common_tags, { Name = "${local.name_prefix}-airflow-key" })
}
resource "local_sensitive_file" "airflow_private_key" {
  count           = local.airflow_count
  content         = tls_private_key.airflow[0].private_key_pem
  filename        = "${path.module}/${local.name_prefix}-airflow-key.pem"
  file_permission = "0600"
}

resource "aws_security_group" "airflow" {
  count       = local.airflow_count
  name        = "${local.name_prefix}-airflow-sg"
  description = "Airflow EC2 access"
  vpc_id      = module.vpc.vpc_id
  ingress {
    description = "Airflow Web UI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = var.airflow_ssh_cidr_blocks
  }
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.airflow_ssh_cidr_blocks
  }
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = merge(local.common_tags, { Name = "${local.name_prefix}-airflow-sg" })
}
resource "aws_security_group" "airflow_rds" {
  count       = local.airflow_count
  name        = "${local.name_prefix}-airflow-rds-sg"
  description = "Airflow PostgreSQL access"
  vpc_id      = module.vpc.vpc_id
  ingress {
    description     = "PostgreSQL from Airflow EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.airflow[0].id]
  }
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = merge(local.common_tags, { Name = "${local.name_prefix}-airflow-rds-sg" })
}

resource "random_password" "airflow_db" {
  count            = local.airflow_count
  length           = 32
  special          = true
  override_special = "!#%&*()-_=+[]{}:?"
}
resource "aws_db_subnet_group" "airflow" {
  count      = local.airflow_count
  name       = "${local.name_prefix}-airflow-db-subnet"
  subnet_ids = module.vpc.private_subnets
  tags       = merge(local.common_tags, { Name = "${local.name_prefix}-airflow-db-subnet" })
}
resource "aws_db_instance" "airflow" {
  count                  = local.airflow_count
  identifier             = "${local.name_prefix}-airflow-postgres"
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  storage_type           = "gp3"
  storage_encrypted      = true
  db_name                = "airflow"
  username               = "airflow"
  password               = random_password.airflow_db[0].result
  db_subnet_group_name   = aws_db_subnet_group.airflow[0].name
  vpc_security_group_ids = [aws_security_group.airflow_rds[0].id]
  publicly_accessible    = false
  multi_az               = false
  skip_final_snapshot    = true
  deletion_protection    = false
  tags                   = merge(local.common_tags, { Name = "${local.name_prefix}-airflow-postgres" })
}

data "aws_iam_policy_document" "airflow_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}
data "aws_iam_policy_document" "airflow_s3" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetBucketLocation", "s3:ListBucket"]
    resources = [local.data_bucket_arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["dags", "dags/*"]
    }
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${local.data_bucket_arn}/dags/*"]
  }
}
resource "aws_iam_role" "airflow" {
  count              = local.airflow_count
  name               = "${local.name_prefix}-airflow-ec2"
  assume_role_policy = data.aws_iam_policy_document.airflow_assume_role.json
  tags               = merge(local.common_tags, { Name = "${local.name_prefix}-airflow-ec2" })
}
resource "aws_iam_role_policy" "airflow_s3" {
  count  = local.airflow_count
  name   = "${local.name_prefix}-airflow-s3"
  role   = aws_iam_role.airflow[0].id
  policy = data.aws_iam_policy_document.airflow_s3.json
}
resource "aws_iam_instance_profile" "airflow" {
  count = local.airflow_count
  name  = "${local.name_prefix}-airflow-profile"
  role  = aws_iam_role.airflow[0].name
  tags  = merge(local.common_tags, { Name = "${local.name_prefix}-airflow-profile" })
}

resource "aws_instance" "airflow" {
  count                       = local.airflow_count
  ami                         = data.aws_ami.airflow_ubuntu.id
  instance_type               = "t3.medium"
  subnet_id                   = module.vpc.public_subnets[0]
  vpc_security_group_ids      = [aws_security_group.airflow[0].id]
  iam_instance_profile        = aws_iam_instance_profile.airflow[0].name
  key_name                    = aws_key_pair.airflow[0].key_name
  associate_public_ip_address = true
  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }
  user_data = templatefile("${path.module}/airflow_user_data.sh.tftpl", {
    db_host                = aws_db_instance.airflow[0].address, db_port = aws_db_instance.airflow[0].port,
    db_name                = aws_db_instance.airflow[0].db_name, db_user = aws_db_instance.airflow[0].username,
    db_password            = random_password.airflow_db[0].result, s3_dags_path = local.airflow_dags_path,
    aws_region             = var.awslogs_region, airflow_admin_username = var.airflow_admin_username,
    airflow_admin_password = var.airflow_admin_password, airflow_admin_email = var.airflow_admin_email,
    airflow_smtp_host      = var.airflow_smtp_host, airflow_smtp_port = var.airflow_smtp_port,
    airflow_smtp_user      = var.airflow_smtp_user, airflow_smtp_password = var.airflow_smtp_password,
    airflow_smtp_mail_from = var.airflow_smtp_mail_from, airflow_smtp_starttls = var.airflow_smtp_starttls,
    airflow_smtp_ssl       = var.airflow_smtp_ssl, airflow_notification_emails = var.airflow_notification_emails,
    airflow_kaggle_backfill_mes = var.airflow_kaggle_backfill_mes
  })
  tags = merge(local.common_tags, { Name = "${local.name_prefix}-airflow" })
}
