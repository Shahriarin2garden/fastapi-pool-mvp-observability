#!/usr/bin/env bash
# Launch the Lightsail demo VM (Ubuntu 24.04, 2 GiB, bundled pricing).
# Lightsail is not covered by the sandbox SCP denies on ec2/iam creation.
# Run from AWS CloudShell (AccountFullAccessRole session).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${LIGHTSAIL_NAME:-fastapi-pool-mvp-demo}"
# Defaults to ap-southeast-2 (the SCP-allowed region for Lightsail); override with
# LIGHTSAIL_REGION. AWS_REGION is ignored on purpose: CloudShell sessions
# default to the console region (e.g. ap-southeast-2) which is SCP-locked.
REGION="${LIGHTSAIL_REGION:-ap-southeast-2}"
AZ="${AZ:-ap-southeast-2a}"
BUNDLE="${BUNDLE:-small_3_2}"        # 2 vCPU / 2 GiB / 60 GB SSD; verify current pricing
BLUEPRINT="${BLUEPRINT:-ubuntu_24_04}"
REPO_URL="${REPO_URL:-https://github.com/Shahriarin2garden/fastapi-pool-mvp-observability.git}"
REPO_BRANCH="${REPO_BRANCH:-observability-assessment}"
ALERT_RECIPIENT="${ALERT_RECIPIENT:-}"
ALLOWED_CIDR="${LIGHTSAIL_ALLOWED_CIDR:-}"

# Refuse an unrestricted cloud firewall. Supply the operator's public IP as /32
# (or an explicitly approved, narrow office/VPN CIDR).
if [[ -z "$ALLOWED_CIDR" ]]; then
  echo "ERROR: set LIGHTSAIL_ALLOWED_CIDR (for example, <your-public-ip>/32)." >&2
  exit 2
fi
python3 - "$ALLOWED_CIDR" <<'PY'
import ipaddress
import sys
try:
    network = ipaddress.ip_network(sys.argv[1], strict=False)
except ValueError as exc:
    raise SystemExit(f"ERROR: invalid LIGHTSAIL_ALLOWED_CIDR: {exc}")
if network.version != 4 or network.prefixlen < 24:
    raise SystemExit("ERROR: LIGHTSAIL_ALLOWED_CIDR must be IPv4 /24 or narrower (for example, a single IP as /32).")
PY

command -v aws >/dev/null 2>&1 || { echo "ERROR: aws CLI not found." >&2; exit 1; }

EXISTING="$(aws lightsail get-instance --instance-name "$NAME" --region "$REGION" --query 'instance.state.name' --output text 2>/dev/null || echo "not-found")"

if [[ "$EXISTING" != "not-found" ]]; then
  echo "Instance '$NAME' already exists (state: $EXISTING)."
  echo "NOTE: user data only applies when an instance is created; run make lightsail-destroy first to pick up template changes."
  if [[ "$EXISTING" == "stopped" ]]; then
    # Resume but continue: the public-port rules below must be re-applied so
    # older instances receive the current restricted allowlist.
    bash "$ROOT/scripts/lightsail-resume.sh"
  fi
fi

db_pass="$(openssl rand -hex 12)"
grafana_pass="$(openssl rand -hex 12)"
CREATED=0

if [[ "$EXISTING" == "not-found" ]]; then
  CREATED=1
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
fi

echo "== Waiting for the instance to reach running state =="
STATE="pending"
for _ in $(seq 1 60); do
  STATE="$(aws lightsail get-instance-state --instance-name "$NAME" --region "$REGION" --query 'state.name' --output text)"
  [[ "$STATE" == "running" ]] && break
  sleep 10
done
if [[ "$STATE" != "running" ]]; then
  echo "ERROR: instance stuck in '$STATE' state after 10 minutes." >&2
  exit 1
fi

echo "== Opening SSH/API/Grafana only to $ALLOWED_CIDR =="
PORTS_JSON="[
    {\"fromPort\": 22, \"toPort\": 22, \"protocol\": \"tcp\", \"cidrs\": [\"$ALLOWED_CIDR\"], \"cidrListAliases\": [\"lightsail-connect\"]},
    {\"fromPort\": 8001, \"toPort\": 8001, \"protocol\": \"tcp\", \"cidrs\": [\"$ALLOWED_CIDR\"]},
    {\"fromPort\": 3000, \"toPort\": 3000, \"protocol\": \"tcp\", \"cidrs\": [\"$ALLOWED_CIDR\"]}
  ]"
for _ in $(seq 1 10); do
  if aws lightsail put-instance-public-ports \
    --instance-name "$NAME" \
    --port-infos "$PORTS_JSON" \
    --region "$REGION" >/dev/null 2>&1; then
    break
  fi
  sleep 15
done

IP="$(aws lightsail get-instance --instance-name "$NAME" --region "$REGION" --query 'instance.publicIpAddress' --output text)"
echo "Public IP: $IP"

if [[ "$CREATED" == "1" ]]; then
  echo "$grafana_pass" > "$ROOT/.lightsail-grafana-password"
  chmod 600 "$ROOT/.lightsail-grafana-password"
fi

if [[ "$CREATED" == "1" ]]; then
  echo "== Waiting for the stack (user-data installs Docker + builds images; up to 20 min) =="
  for _ in $(seq 1 80); do
    if curl -fsS --max-time 5 "http://$IP:8001/health" >/dev/null 2>&1; then
      echo "API is healthy."
      break
    fi
    sleep 15
  done
fi

echo
echo "== Demo URLs =="
echo "  API:     http://$IP:8001/health"
echo "  Grafana: http://$IP:3000  (admin / password in .lightsail-grafana-password)"
echo "  SSH:     Lightsail console 'Connect using SSH' button, or the default key from"
echo "           Account > SSH keys > $REGION (then: ssh -i <key> ubuntu@$IP)"
echo
echo "To stop billing for compute between demos:  make lightsail-stop"
