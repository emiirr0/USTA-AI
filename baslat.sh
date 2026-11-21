#!/usr/bin/env sh
# USTA·AI — macOS / Linux / Raspberry Pi başlatıcı
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
exec "$PY" -m usta "$@"
