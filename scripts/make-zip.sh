#!/usr/bin/env bash
set -euo pipefail
id="${1:?candidate id required}"
zip="${id}_observability.zip"
git archive --format=zip --output="$zip" HEAD
unzip -l "$zip"
if unzip -l "$zip" | grep -E '(^|/)\.env$|password|secret|token' >/dev/null; then
  echo "Potential secret path in archive" >&2
  exit 1
fi
