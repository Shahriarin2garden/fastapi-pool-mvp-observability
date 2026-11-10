#!/usr/bin/env bash
set -euo pipefail
microk8s helm3 uninstall alloy -n monitoring || true
microk8s kubectl delete namespace demo monitoring --ignore-not-found
