# ---------------------------------------------------------------------------
# Data bucket
# ---------------------------------------------------------------------------
# The buckets are managed by the separate IaC/buckets state. The application
# state only reads them and therefore can be destroyed independently.
data "aws_s3_bucket" "data" {
  bucket = local.data_bucket_name
}
