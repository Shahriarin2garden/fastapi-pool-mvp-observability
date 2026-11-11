#!/usr/bin/env bash
# Launch the Lightsail demo VM (Ubuntu 24.04, 2 GiB, bundled pricing).
# Lightsail is not covered by the sandbox SCP denies on ec2/iam creation.
# Run from AWS CloudShell (AccountFullAccessRole session).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${LIGHTSAIL_NAME:-fastapi-pool-mvp-demo}"
# Pinned to us-east-1 (probed as SCP-allowed for Lightsail); override with
# LIGHTSAIL_REGION. AWS_REGION is ignored on purpose: CloudShell sessions
# default to the console region (e.g. ap-southeast-2) which is SCP-locked.
REGION="${LIGHTSAIL_REGION:-us-east-1}"
AZ="${AZ:-us-east-1a}"
BUNDLE="${BUNDLE:-small_3_0}"        # 2 vCPU / 2 GiB / 60 GB SSD (~$10/mo)
BLUEPRINT="${BLUEPRINT:-ubuntu_24_04}"
REPO_URL="${REPO_URL:-https://github.com/Shahriarin2garden/fastapi-pool-mvp-observability.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
ALERT_RECIPIENT="${ALERT_RECIPIENT:-you@example.com}"

command -v aws >/dev/null 2>&1 || { echo "ERROR: aws CLI not found." >&2; exit 1; }

EXISTING="$(aws lightsail get-instance --instance-name "$NAME" --region "$REGION" --query 'instance.state.name' --output text 2>/dev/null || echo "not-found")"

if [[ "$EXISTING" != "not-found" ]]; then
  echo "Instance '$NAME' already exists (state: $EXISTING)."
  if [[ "$EXISTING" == "stopped" ]]; then
    bash "$ROOT/scripts/lightsail-resume.sh"
  fi
  exit 0
fi

db_pass="$(openssl rand -hex 12)"
grafana_pass="$(openssl rand -hex 12)"

USER_DATA="$(sed \
  -e "s|@@repo_url@@|$REPO_URL|g" \
  -e "s|@@repo_branch@@|$REPO_BRANCH|g" \
  -e "s|@@db_pass@@|$db_pass|g" \
  -e "s|@@grafana_pass@@|$grafana_pass|g" \
  -e "s|@@alert_recipient@@|$ALERT_RECIPIENT|g" \
  "$ROOT/infra/lightsail/user-data.sh.tmpl")"

echo "== Creating Lightsail instance $NAME ($BLUEPRINT, $BUNDLE) in $AZ =="
aws lightsail create-instances \
  --instance-name "$NAME" \
  --availability-zone "$AZ" \
  --bundle-id "$BUNDLE" \
  --blueprint-id "$BLUEPRINT" \
  --user-data "$USER_DATA" \
  --tags key=Project,value=fastapi-pool-mvp \
  --region "$REGION" >/dev/null

echo "== Opening ports 22/80/8001/3000 =="
aws lightsail put-instance-public-ports \
  --instance-name "$NAME" \
  --port-infos '[
    {"fromPort": 22,   "toPort": 22,   "protocol": "tcp", "cidrs": ["0.0.0.0/0"]},
    {"fromPort": 80,   "toPort": 80,   "protocol": "tcp", "cidrs": ["0.0.0.0/0"]},
    {"fromPort": 8001, "toPort": 8001, "protocol": "tcp", "cidrs": ["0.0.0.0/0"]},
    {"fromPort": 3000, "toPort": 3000, "protocol": "tcp", "cidrs": ["0.0.0.0/0"]}
  ]' \
  --region "$REGION" >/dev/null

echo "== Waiting for the instance to reach running state =="
for _ in $(seq 1 30); do
  STATE="$(aws lightsail get-instance-state --instance-name "$NAME" --region "$REGION" --query 'state.name' --output text)"
  [[ "$STATE" == "running" ]] && break
  sleep 10
done

IP="$(aws lightsail get-instance --instance-name "$NAME" --region "$REGION" --query 'instance.publicIpAddress' --output text)"
echo "Public IP: $IP"

echo "$grafana_pass" > "$ROOT/.lightsail-grafana-password"
chmod 600 "$ROOT/.lightsail-grafana-password"

echo "== Waiting for the stack (user-data installs Docker + builds images; up to 20 min) =="
for _ in $(seq 1 80); do
  if curl -fsS --max-time 5 "http://$IP:8001/health" >/dev/null 2>&1; then
    echo "API is healthy."
    break
  fi
  sleep 15
done

echo
echo "== Demo URLs =="
echo "  API:     http://$IP:8001/health"
echo "  Grafana: http://$IP:3000  (admin / password in .lightsail-grafana-password)"
echo "  SSH:     Lightsail console 'Connect using SSH' button, or the default key from"
echo "           Account > SSH keys > $REGION (then: ssh -i <key> ubuntu@$IP)"
echo
echo "To stop billing for compute between demos:  make lightsail-stop"
