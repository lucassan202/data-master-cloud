# ---------------------------------------------------------------------------
# IAM roles
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name_prefix}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
  description        = "Least-privilege execution role for the ${local.name_prefix} ECS tasks"

  tags = local.common_tags
}

resource "aws_iam_role" "ecs_task" {
  name               = "${local.name_prefix}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
  description        = "Task role for the ${local.name_prefix} ECS tasks"

  tags = local.common_tags
}

resource "aws_iam_role" "lambda_download" {
  name               = "${local.name_prefix}-lambda-download"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  description        = "Least-privilege role for the ${local.name_prefix} CSV download Lambda"

  tags = local.common_tags
}

resource "aws_iam_role" "lambda_screp" {
  name               = "${local.name_prefix}-lambda-screp"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  description        = "Least-privilege role for the ${local.name_prefix} scraping Lambda"

  tags = local.common_tags
}

data "aws_iam_policy_document" "ecs_execution" {
  statement {
    sid       = "ReadEnvironmentFile"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = [var.s3_env_vars_file_arn]
  }

  statement {
    sid       = "LocateEnvironmentBucket"
    effect    = "Allow"
    actions   = ["s3:GetBucketLocation"]
    resources = ["arn:aws:s3:::${local.s3_bucket_name}"]
  }

  statement {
    sid    = "WriteContainerLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.ecs_selenium.arn}:*"]
  }
}

resource "aws_iam_role_policy" "ecs_execution" {
  name   = "${local.name_prefix}-ecs-execution-policy"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.ecs_execution.json
}

data "aws_iam_policy_document" "lambda_download" {
  statement {
    sid       = "WriteDownloadedFiles"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${local.data_bucket_arn}/tmp/*"]
  }

  statement {
    sid    = "WriteLambdaLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.lambda_download.arn}:*"]
  }
}

resource "aws_iam_role_policy" "lambda_download" {
  name   = "${local.name_prefix}-lambda-download-policy"
  role   = aws_iam_role.lambda_download.id
  policy = data.aws_iam_policy_document.lambda_download.json
}

data "aws_iam_policy_document" "lambda_screp" {
  statement {
    sid    = "ManageNetworkInterfaces"
    effect = "Allow"
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeSubnets",
      "ec2:DeleteNetworkInterface",
      "ec2:AssignPrivateIpAddresses",
      "ec2:UnassignPrivateIpAddresses",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "ReadAndWriteScraperFiles"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${local.data_bucket_arn}/screp/*"]
  }

  statement {
    sid    = "WriteLambdaLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "lambda_screp" {
  name   = "${local.name_prefix}-lambda-screp-policy"
  role   = aws_iam_role.lambda_screp.id
  policy = data.aws_iam_policy_document.lambda_screp.json
}

# The GitHub Actions role remains external to this Terraform state. These
# additional inline policies grant it PassRole for the environment-specific
# roles created above. The existing broad GitHub policies are intentionally
# left untouched.
data "aws_iam_policy_document" "github_actions_passrole" {
  statement {
    sid     = "PassDataMasterRoles"
    effect  = "Allow"
    actions = ["iam:PassRole"]
    resources = concat([
      aws_iam_role.ecs_execution.arn,
      aws_iam_role.ecs_task.arn,
      aws_iam_role.lambda_download.arn,
      aws_iam_role.lambda_screp.arn,
    ], local.airflow_enabled ? [aws_iam_role.airflow[0].arn] : [])
  }
}

resource "aws_iam_role_policy" "github_actions_passrole" {
  name   = "${local.name_prefix}-github-actions-passrole"
  role   = "github-actions-data-master"
  policy = data.aws_iam_policy_document.github_actions_passrole.json
}

output "iam_role_arns" {
  value = {
    ecs_execution   = aws_iam_role.ecs_execution.arn
    ecs_task        = aws_iam_role.ecs_task.arn
    lambda_download = aws_iam_role.lambda_download.arn
    lambda_screp    = aws_iam_role.lambda_screp.arn
  }
}
