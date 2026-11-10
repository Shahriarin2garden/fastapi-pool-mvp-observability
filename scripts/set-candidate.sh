#!/usr/bin/env bash
set -euo pipefail
name="${1:-}"
id="${2:-}"
[[ -n "$name" && -n "$id" ]] || { echo "usage: $0 NAME ID" >&2; exit 2; }
files=(README.md MANUAL_STEPS.md)
for file in "${files[@]}"; do
  sed -i "s/CANDIDATE_NAME/$name/g; s/CANDIDATE_ID/$id/g" "$file"
done
git diff --stat -- "${files[@]}"
