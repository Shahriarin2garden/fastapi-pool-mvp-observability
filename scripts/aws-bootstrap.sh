#!/usr/bin/env bash
# One-time setup of always-on AWS resources (nearly free):
# remote state bucket + lock table, ECR repo, budget and billing alarm.
# Usage: scripts/aws-bootstrap.sh <email-for-alerts> [github_org/repo]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "ERROR: AWS credentials are not configured (try 'aws sso login' or export keys)." >&2
  exit 1
fi

EMAIL="${1:-}"
GITHUB_REPO="${2:-}"
if [[ -z "$EMAIL" ]]; then
  echo "Usage: $0 <email-for-alerts> [github_org/repo]" >&2
  exit 1
fi

REGION="${AWS_REGION:-us-east-1}"

echo "== Applying bootstrap layer (region: $REGION) =="
terraform -chdir="$ROOT/infra/bootstrap" init -input=false -reconfigure
if [[ "${AWS_BOOTSTRAP_PROMPT:-0}" == "1" ]]; then
  terraform -chdir="$ROOT/infra/bootstrap" apply -input=false \
    -var="region=$REGION" \
    -var="budget_email=$EMAIL" \
    -var="github_repo=${GITHUB_REPO:-CANDIDATE_NAME/fastapi-pool-mvp-observability}"
else
  terraform -chdir="$ROOT/infra/bootstrap" apply -input=false -auto-approve \
    -var="region=$REGION" \
    -var="budget_email=$EMAIL" \
    -var="github_repo=${GITHUB_REPO:-CANDIDATE_NAME/fastapi-pool-mvp-observability}"
fi

echo
echo "== Bootstrap complete. Outputs: =="
terraform -chdir="$ROOT/infra/bootstrap" output
echo
echo "SNS topic needs email confirmation: check the inbox for '$EMAIL' and click the subscription link."
