#!/usr/bin/env bash
# Build the order API image, push it to ECR, render the Kubernetes
# manifests and deploy app + Postgres + ALB ingresses to the cluster.
# Requires scripts/aws-up.sh to have been run (reads .env.aws).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/.env.aws"

MANIFESTS="$ROOT/kubernetes/aws/manifests"
RENDER_DIR="$ROOT/kubernetes/.rendered-aws"
IMAGE_TAG="$(git -C "$ROOT" rev-parse --short HEAD)"
IMAGE="${ECR_REPO_URL}:${IMAGE_TAG}"

for tool in docker kubectl aws envsubst; do
  command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: '$tool' is not installed." >&2; exit 1; }
done

echo "== Pushing image to ECR =="
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$(echo "$ECR_REPO_URL" | cut -d/ -f1)"
docker build -t "$IMAGE" "$ROOT"
docker push "$IMAGE"

echo "== Rendering manifests =="
rm -rf "$RENDER_DIR"
mkdir -p "$RENDER_DIR"
SUBST_VARS='${DB_USER} ${DB_PASS} ${DB_NAME} ${IMAGE}'
for template in "$MANIFESTS"/*.tmpl; do
  target="$RENDER_DIR/$(basename "$template" .tmpl)"
  envsubst "$SUBST_VARS" < "$template" > "$target"
done
cp "$MANIFESTS"/*.yaml "$RENDER_DIR"

echo "== Applying manifests =="
kubectl apply -f "$RENDER_DIR"

echo "== Waiting for rollout =="
kubectl -n shop rollout status deployment/postgres --timeout=5m
kubectl -n shop rollout status deployment/order-api --timeout=5m

echo
echo "== Deployed =="
kubectl -n shop get deploy,svc,hpa
kubectl -n shop get ingress order-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'
echo "API:      http://<ALB_HOSTNAME>/health"
echo "Grafana:  http://<ALB_HOSTNAME>/grafana"
