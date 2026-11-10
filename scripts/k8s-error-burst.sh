#!/usr/bin/env bash
set -euo pipefail
if command -v microk8s >/dev/null 2>&1; then
  KUBE=(microk8s kubectl)
else
  KUBE=(kubectl)
fi
"${KUBE[@]}" -n demo exec deploy/log-generator -- sh -c 'for i in 1 2 3 4 5; do echo "level=ERROR event=manual_incident n=$i" > /proc/1/fd/2; done'
