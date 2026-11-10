#!/usr/bin/env bash
set -euo pipefail
pause() { read -r -p "$1 Press ENTER to continue..." _; }
echo "Demo: health endpoint"; curl -fsS http://127.0.0.1:8001/health
pause "Point at the healthy API."
echo "Demo: one normal order"; curl -fsS -X POST http://127.0.0.1:8001/api/orders -H 'content-type: application/json' -d '{"customer_email":"demo@example.com","item":"widget","quantity":1,"amount_cents":199}'
pause "Point at the order and business metrics."
scripts/traffic-test.sh burst
pause "Point at request rate and p95."
scripts/traffic-test.sh failure
pause "Point at the failure-rate panel."
scripts/k8s-error-burst.sh || true
microk8s kubectl -n demo logs deploy/log-generator --tail=10 || true
echo "URLs: Grafana http://127.0.0.1:3000/d/obs-metrics, Prometheus http://127.0.0.1:9090/targets"
pause "Point at Loki Explore with {namespace=\"demo\"} and |= \"ERROR\"."
read -r -p "Run the alert test? [y/N] " answer
[[ "$answer" == y || "$answer" == Y ]] && scripts/alert-test.sh || true
