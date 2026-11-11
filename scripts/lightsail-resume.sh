#!/usr/bin/env bash
# Start the stopped Lightsail VM. The dynamic public IP may change.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${LIGHTSAIL_NAME:-fastapi-pool-mvp-demo}"
REGION="${LIGHTSAIL_REGION:-us-east-1}"

echo "Starting $NAME ..."
aws lightsail start-instance --instance-name "$NAME" --region "$REGION" >/dev/null
for _ in $(seq 1 30); do
  STATE="$(aws lightsail get-instance-state --instance-name "$NAME" --region "$REGION" --query 'state.name' --output text)"
  [[ "$STATE" == "running" ]] && break
  sleep 5
done

IP="$(aws lightsail get-instance --instance-name "$NAME" --region "$REGION" --query 'instance.publicIpAddress' --output text)"
echo "Running again:"
echo "  API:     http://$IP:8001/health"
echo "  Grafana: http://$IP:3000  (password in $ROOT/.lightsail-grafana-password)"
