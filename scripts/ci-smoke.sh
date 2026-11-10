#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $1" >&2
  docker compose logs --tail=200
  exit 1
}

if [[ "$(docker compose ps --status running --services | grep -Fx grafana || true)" != "grafana" ]]; then
  docker compose logs grafana
  fail "Grafana failed to start (check alert provisioning YAML)"
fi

order_payload='{"customer_email":"smoke@example.com","item":"smoke-test","quantity":1,"amount_cents":100}'
order_status="$(curl -sS -o /dev/null -w '%{http_code}' \
  -H 'Content-Type: application/json' -d "$order_payload" \
  http://127.0.0.1:8001/api/orders)" || fail "POST /api/orders request failed"
[[ "$order_status" == "201" ]] || fail "POST /api/orders expected 201, got $order_status"

failure_status="$(curl -sS -o /dev/null -w '%{http_code}' \
  -H 'Content-Type: application/json' -d "$order_payload" \
  'http://127.0.0.1:8001/api/orders?simulate_failure=true')" || fail "POST /api/orders?simulate_failure=true request failed"
[[ "$failure_status" == "500" ]] || fail "POST /api/orders?simulate_failure=true expected 500, got $failure_status"

metrics="$(curl -fsS http://127.0.0.1:8001/metrics)" || fail "GET /metrics request failed"
grep -q 'orders_created_total' <<<"$metrics" || fail "GET /metrics missing orders_created_total"
grep -q 'order_request_duration_seconds_bucket' <<<"$metrics" || fail "GET /metrics missing order_request_duration_seconds_bucket"

targets_url='http://127.0.0.1:9090/api/v1/targets'
targets_ok=false
for _ in $(seq 1 30); do
  targets="$(curl -fsS "$targets_url" || true)"
  if jq -e '
    [.data.activeTargets[] |
      select(.labels.job == "node-exporter" or .labels.job == "order-api") |
      .health] as $health |
    ($health | index("up")) != null and
    ($health | length) == 2 and
    ($health | all(. == "up"))
  ' <<<"$targets" >/dev/null 2>&1; then
    targets_ok=true
    break
  fi
  sleep 2
done
[[ "$targets_ok" == true ]] || fail "Prometheus targets did not show node-exporter and order-api healthy"

datasources="$(curl -fsS -u "${GF_ADMIN_USER}:${GF_ADMIN_PASSWORD}" \
  http://127.0.0.1:3000/api/datasources)" || fail "Grafana datasources request failed"
[[ "$(jq 'length' <<<"$datasources" 2>/dev/null || echo 0)" == "2" ]] ||
  fail "Grafana /api/datasources expected 2 datasources"

dashboards="$(curl -fsS -u "${GF_ADMIN_USER}:${GF_ADMIN_PASSWORD}" \
  'http://127.0.0.1:3000/api/search?type=dash-db')" || fail "Grafana dashboard search failed"
[[ "$(jq 'length' <<<"$dashboards" 2>/dev/null || echo 0)" == "2" ]] ||
  fail "Grafana /api/search?type=dash-db expected 2 dashboards"

rules="$(curl -fsS -u "${GF_ADMIN_USER}:${GF_ADMIN_PASSWORD}" \
  http://127.0.0.1:3000/api/v1/provisioning/alert-rules)" || fail "Grafana alert rules request failed"
grep -q 'OrderAPIDown' <<<"$rules" || fail "Grafana alert rules missing OrderAPIDown"
[[ "$(jq 'length' <<<"$rules" 2>/dev/null || echo 0)" -gt 0 ]] ||
  fail "Grafana alert rules list is empty"

echo "PASS: CI smoke checks"
