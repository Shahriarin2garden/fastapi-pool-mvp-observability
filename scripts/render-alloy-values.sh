#!/usr/bin/env bash
set -euo pipefail
host="${1:-${LOKI_BIND_IP:-}}"
if [[ -z "$host" || "$host" == "127.0.0.1" || "$host" == "localhost" ]]; then
  echo "Provide the laptop IP reachable from MicroK8s pods; loopback is not reachable." >&2
  exit 1
fi
mkdir -p kubernetes/.rendered
sed "s/__LOKI_HOST__/${host}/g" kubernetes/alloy-values.yaml > kubernetes/.rendered/alloy-values.yaml
echo "Rendered kubernetes/.rendered/alloy-values.yaml"
echo "microk8s helm3 install alloy grafana/alloy -n monitoring --create-namespace -f kubernetes/.rendered/alloy-values.yaml"
