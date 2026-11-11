data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id

  state_bucket_name = "${var.project}-tfstate-${local.account_id}-${var.region}"
  lock_table_name   = "${var.project}-tfstate-lock-${local.account_id}"
  ecr_repo_name     = "${var.project}/order-api"
}
