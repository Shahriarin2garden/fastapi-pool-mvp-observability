#!/usr/bin/env bash
# Spin up the ephemeral EKS demo stack (VPC, EKS with spot nodes, ALB
# controller, metrics-server, kube-prometheus-stack, Loki, Alloy).
# Everything here bills per hour: bring it down with scripts/aws-down.sh.
# Set AWS_UP_YES=1 to skip the apply confirmation prompt.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${PROJECT:-fastapi-pool-mvp}"
REGION="${AWS_REGION:-us-east-1}"
CLUSTER_DIR="$ROOT/infra/cluster"

for tool in terraform kubectl aws openssl; do
  command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: '$tool' is not installed." >&2; exit 1; }
done

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "ERROR: AWS credentials are not configured (try 'aws sso login' or export keys)." >&2
  exit 1
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
STATE_BUCKET="${PROJECT}-tfstate-${ACCOUNT_ID}-${REGION}"
LOCK_TABLE="${PROJECT}-tfstate-lock-${ACCOUNT_ID}"

if ! aws s3api head-bucket --bucket "$STATE_BUCKET" 2>/dev/null; then
  echo "ERROR: state bucket '$STATE_BUCKET' not found. Run 'make aws-bootstrap' first." >&2
  exit 1
fi

echo "== Initializing cluster layer backend =="
terraform -chdir="$CLUSTER_DIR" init -input=false -reconfigure \
  -backend-config="bucket=$STATE_BUCKET" \
  -backend-config="dynamodb_table=$LOCK_TABLE" \
  -backend-config="region=$REGION"

echo "== Applying cluster layer (this creates hourly-billed resources) =="
if [[ "${AWS_UP_YES:-0}" == "1" ]]; then
  terraform -chdir="$CLUSTER_DIR" apply -input=false -auto-approve
else
  terraform -chdir="$CLUSTER_DIR" apply -input=false
fi

CLUSTER_NAME="$(terraform -chdir="$CLUSTER_DIR" output -raw cluster_name)"
ECR_REPO_URL="$(terraform -chdir="$CLUSTER_DIR" output -raw ecr_repository_url)"
DB_PASS="$(openssl rand -hex 12)"

cat > "$ROOT/.env.aws" <<EOF
AWS_REGION=$REGION
AWS_CLUSTER_NAME=$CLUSTER_NAME
ECR_REPO_URL=$ECR_REPO_URL
DB_USER=postgres
DB_NAME=fastdb
DB_PASS=$DB_PASS
EOF
chmod 600 "$ROOT/.env.aws"

aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

echo "== Waiting for nodes to become Ready =="
kubectl wait --for=condition=Ready nodes --all --timeout=600s

echo
echo "== Stack is up. Next steps =="
echo "  make aws-deploy      # build, push to ECR and deploy app + monitoring ingresses"
echo "  make aws-down        # tear down (stops the hourly billing)"
