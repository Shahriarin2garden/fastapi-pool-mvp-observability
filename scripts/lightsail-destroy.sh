#!/usr/bin/env bash
# Delete the Lightsail VM and its disk. Full teardown.
# Usage: scripts/lightsail-destroy.sh [CONFIRM=yes]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${LIGHTSAIL_NAME:-fastapi-pool-mvp-demo}"
REGION="${LIGHTSAIL_REGION:-ap-southeast-2}"

if [[ "${CONFIRM:-no}" != "yes" ]]; then
  read -r -p "Type 'destroy' to delete instance '$NAME' (all data on it is lost): " answer
  [[ "$answer" == "destroy" ]] || { echo "Aborted." >&2; exit 1; }
fi

aws lightsail delete-instance --instance-name "$NAME" --region "$REGION" >/dev/null
rm -f "$ROOT/.lightsail-grafana-password"
echo "Lightsail instance '$NAME' deleted."
