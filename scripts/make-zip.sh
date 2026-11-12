#!/usr/bin/env bash
set -euo pipefail

id="${1:?candidate id required}"
zip="${id}_observability.zip"

git archive --format=zip --output="$zip" HEAD
unzip -l "$zip"

if ! unzip -Z1 "$zip" | grep -qE '(^|/)evidence/'; then
  echo "Evidence folder is missing from archive" >&2
  exit 1
fi

# Allow the committed example env files, but reject real env files and common
# credential, private-key, and Terraform-state artifacts even if force-added.
unsafe_paths="$(unzip -Z1 "$zip" | awk '
{
  path = $0
  name = path
  sub(/^.*\//, "", name)
  lower = tolower(path)

  if ((name ~ /^\.env($|\.)/ && name != ".env.example") ||
      lower ~ /(^|\/)\.aws\/credentials$/ ||
      lower ~ /(^|\/)\.lightsail-grafana-password$/ ||
      lower ~ /(^|\/)\.ec2-grafana-password$/ ||
      lower ~ /(^|\/)(id_rsa|id_ed25519)$/ ||
      lower ~ /\.(pem|p12|pfx|tfstate|tfplan)(\.backup)?$/ ||
      lower ~ /(password|secret|token)/) {
    print path
  }
}')"

if [[ -n "$unsafe_paths" ]]; then
  echo "Potential secret or private infrastructure artifact found in archive:" >&2
  printf '%s\n' "$unsafe_paths" >&2
  exit 1
fi

echo "Archive passed path-based secret checks: $zip"
