#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ./run.sh <script.py> [args...]"
  exit 1
fi

SCRIPT="$1"
shift

if [[ ! -f "$SCRIPT" ]]; then
  echo "Script not found: $SCRIPT"
  exit 1
fi

exec uv run "$SCRIPT" "$@"
