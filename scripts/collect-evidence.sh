#!/usr/bin/env bash
set -euo pipefail
mkdir -p evidence
out="evidence/$(date -u +%Y%m%dT%H%M%SZ).txt"
{
  date -u
  command -v lsb_release >/dev/null && lsb_release -a || cat /etc/os-release
  docker --version || true
  docker compose version || true
  docker compose config 2>/dev/null | sed -E 's/(PASSWORD|SMTP_[A-Z_]+|DB_PASS):.*/\1: REDACTED/g' || true
  docker compose ps || true
  microk8s status --wait-ready || true
  microk8s kubectl get nodes || true
  microk8s kubectl get pods -A || true
  microk8s kubectl -n demo logs deploy/log-generator --tail=50 || true
  scripts/crosscheck.sh || true
  curl -fsS http://127.0.0.1:8001/metrics | grep -E 'orders_created|order_request' || true
} > "$out"
echo "$out"
