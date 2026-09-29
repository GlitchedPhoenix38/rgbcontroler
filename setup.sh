#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install it with: sudo apt install python3"
  exit 1
fi

python3 - <<'PY'
import tkinter
print("Tkinter is available")
PY

echo "No third-party Python packages are required."
echo "Run with: sudo python3 main.py"
