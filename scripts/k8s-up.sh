#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then
  set -a
  . ./.env
  set +a
fi
: "${LOKI_BIND_IP:?Set LOKI_BIND_IP to the laptop IP in .env}"
[[ "$LOKI_BIND_IP" != 127.0.0.1 && "$LOKI_BIND_IP" != localhost ]] || {
  echo "LOKI_BIND_IP must be reachable from MicroK8s, not loopback." >&2
  exit 1
}
microk8s kubectl apply -f kubernetes/namespace.yaml -f kubernetes/workload.yaml
microk8s kubectl -n demo rollout status deployment/log-generator --timeout=120s
scripts/render-alloy-values.sh "$LOKI_BIND_IP"
microk8s helm3 repo add grafana https://grafana.github.io/helm-charts 2>/dev/null || true
microk8s helm3 repo update
microk8s helm3 upgrade --install alloy grafana/alloy -n monitoring --create-namespace -f kubernetes/.rendered/alloy-values.yaml
microk8s kubectl -n monitoring wait --for=condition=ready pod -l app.kubernetes.io/name=alloy --timeout=180s
microk8s kubectl run curltest --rm -i --restart=Never --image=curlimages/curl -- curl -fsS "http://${LOKI_BIND_IP}:3100/ready"
