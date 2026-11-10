#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then
  set -a
  . ./.env
  set +a
fi
trap 'docker compose start app >/dev/null 2>&1 || true' EXIT
trap 'exit 130' INT TERM
if [[ "${1:-}" == "--high-failure" ]]; then
  scripts/traffic-test.sh failure
  echo "High-failure traffic generated. Check HighOrderFailureRate in Grafana."
  exit 0
fi
docker compose ps
curl -fsS http://127.0.0.1:8001/health >/dev/null
docker compose stop app
echo "Waiting up to five minutes for OrderAPIDown. Check Grafana and email."
started_at=$SECONDS
last_response=""
for _ in $(seq 1 30); do
  last_response="$(curl -fsS -u "${GF_ADMIN_USER}:${GF_ADMIN_PASSWORD}" \
    http://127.0.0.1:3000/api/alertmanager/grafana/api/v2/alerts 2>/dev/null || true)"
  if command -v jq >/dev/null 2>&1; then
    active_order_api_down="$(jq -e \
      '[.[] | select(.labels.alertname=="OrderAPIDown" and .status.state=="active")] | length > 0' \
      <<<"$last_response" 2>/dev/null || false)"
  else
    active_order_api_down=false
    if grep -q 'OrderAPIDown' <<<"$last_response" &&
      grep -Eq '"state"[[:space:]]*:[[:space:]]*"active"' <<<"$last_response"; then
      active_order_api_down=true
    fi
  fi
  if [[ "$active_order_api_down" == true ]]; then
    echo "OrderAPIDown is active after $((SECONDS - started_at)) seconds."
    exit 0
  fi
  sleep 10
done
echo "Timed out waiting for active OrderAPIDown alert. Last API response:"
printf '%s\n' "$last_response"
docker compose ps
exit 1
