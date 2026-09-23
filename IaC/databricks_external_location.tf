# ---------------------------------------------------------------------------
# Unity Catalog access to the environment data bucket
# ---------------------------------------------------------------------------

data "aws_caller_identity" "databricks_external_location" {}

locals {
  databricks_external_role_name = "${local.name_prefix}-databricks-s3"
  databricks_external_role_arn  = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.databricks_external_location.account_id}:role/${local.databricks_external_role_name}"
}

data "aws_partition" "current" {}

# The role ARN is deterministic, so the credential can be created before the
# role trust policy is updated with the external ID returned by Databricks.
resource "aws_iam_role" "databricks_external_data" {
  name               = local.databricks_external_role_name
  assume_role_policy = data.aws_iam_policy_document.databricks_external_data_trust.json
  description        = "Unity Catalog access to ${local.data_bucket_name}"

  tags = merge(local.common_tags, {
    Purpose = "Databricks Unity Catalog external location"
  })
}

data "aws_iam_policy_document" "databricks_external_data_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = [databricks_storage_credential.data.aws_iam_role[0].unity_catalog_iam_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [databricks_storage_credential.data.aws_iam_role[0].external_id]
    }
  }

  statement {
    sid     = "SelfAssume"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.databricks_external_location.account_id}:root"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:PrincipalArn"
      values   = [local.databricks_external_role_arn]
    }
  }
}

data "aws_iam_policy_document" "databricks_external_data" {
  statement {
    sid    = "ListDataBucket"
    effect = "Allow"
    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
    ]
    resources = [local.data_bucket_arn]
  }

  statement {
    sid    = "ReadWriteDataObjects"
    effect = "Allow"
    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:ListMultipartUploadParts",
      "s3:PutObject",
    ]
    resources = ["${local.data_bucket_arn}/*"]
  }

  statement {
    sid       = "SelfAssume"
    effect    = "Allow"
    actions   = ["sts:AssumeRole"]
    resources = [local.databricks_external_role_arn]
  }
}

resource "aws_iam_role_policy" "databricks_external_data" {
  name   = "${local.name_prefix}-databricks-s3"
  role   = aws_iam_role.databricks_external_data.id
  policy = data.aws_iam_policy_document.databricks_external_data.json
}

resource "databricks_storage_credential" "data" {
  name = "${var.env}-data-master-credential"

  aws_iam_role {
    role_arn = local.databricks_external_role_arn
  }

  comment = "Managed by Terraform for ${local.data_bucket_name}"
}

resource "databricks_external_location" "data" {
  name               = "${var.env}-data-master"
  url                = "s3://${local.data_bucket_name}"
  credential_name    = databricks_storage_credential.data.id
  comment            = "Managed by Terraform for ${local.data_bucket_name}"
  skip_validation    = true
  enable_file_events = false
  force_destroy      = true

  # Databricks validates the S3 URL during creation. Ensure the role policy
  # is attached before that validation runs.
  depends_on = [aws_iam_role_policy.databricks_external_data]
}

resource "databricks_grants" "data_external_location" {
  external_location = databricks_external_location.data.id

  grant {
    principal  = var.databricks_grant_principal
    privileges = ["READ_FILES", "WRITE_FILES"]
  }
}

output "databricks_external_location" {
  value = {
    name = databricks_external_location.data.name
    url  = databricks_external_location.data.url
  }
}
