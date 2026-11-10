#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://127.0.0.1:8001}"
phase="${1:-all}"
payload='{"customer_email":"demo@example.com","item":"widget","quantity":1,"amount_cents":199}'
metrics() { curl -fsS "$BASE_URL/metrics" | grep -E '^(orders_created_total|order_request_duration_seconds_count)' || true; }
normal() { for _ in {1..5}; do curl -fsS -X POST "$BASE_URL/api/orders" -H 'content-type: application/json' -d "$payload" >/dev/null; done; }
burst() {
  for _ in $(seq "${DURATION:-30}"); do
    seq "${RATE:-20}" | xargs -P "${RATE:-20}" -I{} sh -c "curl -fsS -X POST '$BASE_URL/api/orders' -H 'content-type: application/json' -d '$payload' >/dev/null || true"
    sleep 1
  done
}
failure() { for _ in {1..30}; do curl -sS -X POST "$BASE_URL/api/orders?simulate_failure=true" -H 'content-type: application/json' -d "$payload" >/dev/null; done; curl -sS -X POST "$BASE_URL/api/orders" -H 'content-type: application/json' -d '{"item":""}' >/dev/null || true; }
run() { echo "Before $1"; metrics; "$2"; echo "After $1"; metrics; }
case "$phase" in normal) run normal normal;; burst) run burst burst;; failure) run failure failure;; all) run normal normal; run burst burst; run failure failure;; *) echo "usage: $0 [normal|burst|failure|all]" >&2; exit 2;; esac
