#!/usr/bin/env bash
set -euo pipefail
commands=(
  "sudo apt-get update"
  "sudo apt-get install -y ca-certificates curl gnupg"
  "sudo install -m 0755 -d /etc/apt/keyrings"
  "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg"
  "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable\" | sudo tee /etc/apt/sources.list.d/docker.list"
  "sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
  "sudo snap install microk8s --classic"
  "sudo usermod -aG microk8s,docker \"$USER\""
  "microk8s enable dns helm3"
)
if [[ "${1:-}" != "--yes" ]]; then
  printf '%s\n' "Dry run; review these commands. Re-run with --yes to execute:"
  printf '  %s\n' "${commands[@]}"
  exit 0
fi
for command in "${commands[@]}"; do
  bash -c "$command"
done
