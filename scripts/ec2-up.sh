#!/usr/bin/env bash
# Launch the EC2 demo instance (Ubuntu 24.04 + Docker + full compose stack).
# Run from AWS CloudShell (where the AccountFullAccessRole credentials live).
# Set AWS_EC2_YES=1 to skip the apply confirmation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/ec2"
REGION="${AWS_REGION:-us-east-1}"
VPC_ID="${VPC_ID:-vpc-0a48b6836ade7f854}"

for tool in terraform aws; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "ERROR: '$tool' not found. In CloudShell install terraform:" >&2
    echo "  curl -sLo /tmp/tf.zip https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip && cd /tmp && unzip -o tf.zip && mkdir -p ~/bin && install terraform ~/bin/" >&2
    exit 1
  }
done

if [[ "$(aws configure get region 2>/dev/null || echo "")" != "$REGION" ]]; then
  aws configure set region "$REGION"
fi

echo "== Resolving internet gateway for VPC $VPC_ID =="
IGW_ID="$(aws ec2 describe-internet-gateways \
  --filters Name=attachment.vpc-id,Values="$VPC_ID" \
  --query 'length(InternetGateways)' --output text)"

if [[ "$IGW_ID" == "0" ]]; then
  echo "No IGW attached; Terraform will create one."
  IGW_ARG=""
else
  IGW_ID="$(aws ec2 describe-internet-gateways \
    --filters Name=attachment.vpc-id,Values="$VPC_ID" \
    --query 'InternetGateways[0].InternetGatewayId' --output text)"
  echo "Using existing IGW: $IGW_ID"
  IGW_ARG="-var=internet_gateway_id=$IGW_ID"
fi

echo "== Applying EC2 layer =="
terraform -chdir="$TF_DIR" init -input=false -reconfigure
if [[ "${AWS_EC2_YES:-0}" == "1" ]]; then
  terraform -chdir="$TF_DIR" apply -input=false -auto-approve $IGW_ARG
else
  terraform -chdir="$TF_DIR" apply -input=false $IGW_ARG
fi

PUBLIC_IP="$(terraform -chdir="$TF_DIR" output -raw public_ip)"
echo
echo "== Instance launched =="
echo "Saving SSH key + credentials locally:"
terraform -chdir="$TF_DIR" output -raw private_key_pem > "$ROOT/fastapi-pool-mvp-demo-key.pem"
chmod 600 "$ROOT/fastapi-pool-mvp-demo-key.pem"
terraform -chdir="$TF_DIR" output -raw grafana_admin_password > "$ROOT/.ec2-grafana-password"
chmod 600 "$ROOT/.ec2-grafana-password"
echo "  key:     $ROOT/fastapi-pool-mvp-demo-key.pem"
echo "  grafana: $ROOT/.ec2-grafana-password"

echo "== Waiting for cloud-init + stack to come up (up to 15 min) =="
for _ in $(seq 1 60); do
  if curl -fsS --max-time 5 "http://$PUBLIC_IP:8001/health" >/dev/null 2>&1; then
    echo "API is healthy."
    break
  fi
  sleep 15
done

echo
echo "== Demo URLs =="
echo "  API:     http://$PUBLIC_IP:8001/health"
echo "  Grafana: http://$PUBLIC_IP:3000"
echo "  SSH:     ssh -i $ROOT/fastapi-pool-mvp-demo-key.pem ec2-user@$PUBLIC_IP"
echo
echo "To save money between demos:  make ec2-stop"
