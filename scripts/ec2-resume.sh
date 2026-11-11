#!/usr/bin/env bash
# Start the stopped demo instance again. Note: the public IP changes.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/ec2"

INSTANCE_ID="$(terraform -chdir="$TF_DIR" output -raw instance_id)"
echo "Starting $INSTANCE_ID ..."
aws ec2 start-instances --instance-ids "$INSTANCE_ID" --output text --query 'StartingInstances[].CurrentState.Name' >/dev/null
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

# Refresh the IP in Terraform state, then re-read the outputs.
terraform -chdir="$TF_DIR" apply -input=false -auto-approve -refresh-only >/dev/null
PUBLIC_IP="$(terraform -chdir="$TF_DIR" output -raw public_ip)"

echo "Running again:"
echo "  API:     http://$PUBLIC_IP:8001/health"
echo "  Grafana: http://$PUBLIC_IP:3000"
echo "  SSH:     ssh -i $ROOT/fastapi-pool-mvp-demo-key.pem ec2-user@$PUBLIC_IP"
