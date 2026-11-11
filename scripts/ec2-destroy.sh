#!/usr/bin/env bash
# Terminate the demo instance and delete the EC2 layer resources.
# Usage: scripts/ec2-destroy.sh [CONFIRM=yes]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/ec2"

if [[ "${CONFIRM:-no}" != "yes" ]]; then
  read -r -p "Type 'destroy' to terminate the instance and delete volumes/subnet: " answer
  [[ "$answer" == "destroy" ]] || { echo "Aborted." >&2; exit 1; }
fi

terraform -chdir="$TF_DIR" destroy -input=false -auto-approve
rm -f "$ROOT/fastapi-pool-mvp-demo-key.pem" "$ROOT/.ec2-grafana-password"
echo "EC2 layer destroyed."
