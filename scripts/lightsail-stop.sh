#!/usr/bin/env bash
# Stop the Lightsail VM: compute billing pauses, disk keeps its contents.
set -euo pipefail

NAME="${LIGHTSAIL_NAME:-fastapi-pool-mvp-demo}"
REGION="${AWS_REGION:-us-east-1}"

echo "Stopping $NAME ..."
aws lightsail stop-instance --instance-name "$NAME" --region "$REGION" >/dev/null
for _ in $(seq 1 30); do
  STATE="$(aws lightsail get-instance-state --instance-name "$NAME" --region "$REGION" --query 'state.name' --output text)"
  [[ "$STATE" == "stopped" ]] && break
  sleep 5
done
echo "Stopped. Resume later with: make lightsail-resume"
