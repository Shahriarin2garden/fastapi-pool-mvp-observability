#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then
  set -a
  . ./.env
  set +a
fi
cleanup() { docker compose start app >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM
if [[ "${1:-}" == "--high-failure" ]]; then
  scripts/traffic-test.sh failure
  echo "High-failure traffic generated. Check HighOrderFailureRate in Grafana."
  exit 0
fi
docker compose ps
curl -fsS http://127.0.0.1:8001/health >/dev/null
docker compose stop app
echo "Waiting up to five minutes for OrderAPIDown. Check Grafana and email."
for _ in $(seq 1 20); do
  state="$(curl -fsS -u "${GF_ADMIN_USER}:${GF_ADMIN_PASSWORD}" http://127.0.0.1:3000/api/alertmanager/grafana/api/v2/alerts 2>/dev/null || true)"
  if grep -q 'OrderAPIDown' <<<"$state" && grep -q '"status":"firing"' <<<"$state"; then
    echo "OrderAPIDown is firing."
    break
  fi
  sleep 15
done
read -r -p "Press ENTER after checking the inbox to restore the app..."
docker compose start app
echo "Application restored; verify the alert resolves."
