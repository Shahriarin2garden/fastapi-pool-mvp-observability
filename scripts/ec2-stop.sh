#!/usr/bin/env bash
# Stop the demo instance (EBS volume persists, hourly billing stops).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/ec2"

INSTANCE_ID="$(terraform -chdir="$TF_DIR" output -raw instance_id)"
echo "Stopping $INSTANCE_ID ..."
aws ec2 stop-instances --instance-ids "$INSTANCE_ID" --output text --query 'StoppingInstances[].CurrentState.Name'
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"
echo "Stopped. Resume later with: make ec2-resume"
