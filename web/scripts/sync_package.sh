#!/usr/bin/env bash
# Copy the laughstack package (and its default config) into functions/ so
# `firebase deploy` ships the current pipeline. Run from anywhere.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/src/laughstack"
DST="$ROOT/web/functions/laughstack"

rm -rf "$DST"
cp -r "$SRC" "$DST"
cp "$ROOT/config/default.yaml" "$DST/_default_config.yaml"
find "$DST" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
echo "synced $SRC -> $DST"
