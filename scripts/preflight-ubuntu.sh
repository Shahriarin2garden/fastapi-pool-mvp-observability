#!/usr/bin/env bash
set -euo pipefail
warn=0
fail=0
pass() { echo "PASS: $*"; }
warn() { echo "WARN: $*"; warn=$((warn + 1)); }
fail() { echo "FAIL: $*"; fail=$((fail + 1)); }
if [[ -f /etc/os-release ]]; then
  . /etc/os-release
  [[ "${ID:-}" == ubuntu ]] && pass "Ubuntu detected: ${VERSION_ID}" || warn "Ubuntu 26.04 is the documented target"
else
  fail "Cannot read /etc/os-release"
fi
command -v docker >/dev/null 2>&1 && pass "Docker installed" || fail "Docker is missing"
docker compose version >/dev/null 2>&1 && pass "Compose plugin available" || fail "Docker Compose plugin is missing"
id -nG | grep -qw docker && pass "User is in docker group" || warn "User is not in docker group"
command -v microk8s >/dev/null 2>&1 && microk8s status --wait-ready >/dev/null 2>&1 && pass "MicroK8s ready" || warn "MicroK8s unavailable or not ready"
command -v microk8s >/dev/null 2>&1 && microk8s helm3 version >/dev/null 2>&1 && pass "MicroK8s Helm available" || warn "MicroK8s Helm unavailable"
for port in 8001 3000 9090 3100 9100; do
  ss -ltn "( sport = :$port )" | grep -q LISTEN && warn "Port $port is already in use" || pass "Port $port is available"
done
docker0_ip="$(ip -4 addr show docker0 2>/dev/null | awk '/inet / {print $2; exit}' || true)"
[[ -n "$docker0_ip" ]] && pass "docker0 address: $docker0_ip" || warn "docker0 missing; use 0.0.0.0 with a firewall rule for Node Exporter"
if [[ ! -f .env ]]; then
  fail ".env is missing"
else
  for variable in DB_PASS GF_ADMIN_PASSWORD SMTP_HOST SMTP_USER SMTP_PASSWORD SMTP_FROM_ADDRESS ALERT_RECIPIENT LOKI_BIND_IP; do
    value="$(grep "^${variable}=" .env | cut -d= -f2- || true)"
    [[ -n "$value" && "$value" != "change-me" ]] || fail "$variable is blank or a placeholder"
  done
  pass ".env required values are populated"
fi
command -v hostname >/dev/null 2>&1 && echo "LAN IP candidates: $(hostname -I 2>/dev/null || true)"
command -v ufw >/dev/null 2>&1 && ufw status | head -n 3 || warn "ufw is unavailable"
if (( fail > 0 )); then
  echo "VERDICT: FAIL ($fail failures, $warn warnings). Fix failures, then run make preflight."
  exit 1
fi
echo "VERDICT: PASS ($warn warnings). Next: make up"
