#!/usr/bin/env bash
# Tear down the ephemeral cluster layer (stops the hourly billing).
# The bootstrap layer (state bucket, ECR, budget) is kept.
# Usage: scripts/aws-down.sh [CONFIRM=yes]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${PROJECT:-fastapi-pool-mvp}"
REGION="${AWS_REGION:-us-east-1}"
CLUSTER_DIR="$ROOT/infra/cluster"

if [[ "${CONFIRM:-no}" != "yes" ]]; then
  echo "This DESTROYS the EKS cluster, ALB, node group and all data (including the in-cluster Postgres volume)."
  read -r -p "Type 'destroy' to continue: " answer
  [[ "$answer" == "destroy" ]] || { echo "Aborted." >&2; exit 1; }
fi

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "ERROR: AWS credentials are not configured." >&2
  exit 1
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
STATE_BUCKET="${PROJECT}-tfstate-${ACCOUNT_ID}-${REGION}"
LOCK_TABLE="${PROJECT}-tfstate-lock-${ACCOUNT_ID}"

terraform -chdir="$CLUSTER_DIR" init -input=false -reconfigure \
  -backend-config="bucket=$STATE_BUCKET" \
  -backend-config="dynamodb_table=$LOCK_TABLE" \
  -backend-config="region=$REGION" >/dev/null

# Delete app data first: the in-cluster Postgres PVC is not Terraform-managed.
if kubectl get namespace shop >/dev/null 2>&1; then
  echo "== Deleting shop namespace (app + Postgres data) =="
  kubectl delete namespace shop --wait=true --timeout=5m
fi

# Give the ALB controller time to remove load balancers before VPC teardown.
echo "== Waiting for ingress clean-up =="
for ingress in "shop/order-api" "monitoring/grafana"; do
  kubectl delete ingress "$ingress" --ignore-not-found --wait=true --timeout=3m 2>/dev/null || true
done
sleep 30

echo "== Destroying cluster layer =="
terraform -chdir="$CLUSTER_DIR" destroy -input=false -auto-approve

echo
echo "== Cluster layer destroyed. =="
echo "Keep-alive reminders: state bucket, lock table, ECR and budget stay in place (pennies/month)."
