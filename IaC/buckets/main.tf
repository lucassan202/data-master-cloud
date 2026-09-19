locals {
  bucket_name = "${var.env}-${var.aws_region}-data-master"
}

resource "aws_s3_bucket" "data" {
  bucket = local.bucket_name

  lifecycle {
    prevent_destroy = true
  }
}
