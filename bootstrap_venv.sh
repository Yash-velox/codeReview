#!/usr/bin/env bash
# Create .venv and install dependencies using the venv's Python explicitly
# (avoids Debian PEP 668 "externally-managed-environment" when `pip` points at system pip).
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"

echo "Using interpreter: $($PY --version 2>&1)"

if [[ ! -d .venv ]]; then
  "$PY" -m venv .venv
fi

VP=".venv/bin/python"
if [[ ! -x "$VP" ]]; then
  echo "error: missing $VP — install: sudo apt install python3.12-venv (or python3.xx-venv for your Python)" >&2
  exit 1
fi

# Ensure pip exists inside the venv (some minimal Ubuntu images ship venv without pip)
if ! "$VP" -m pip --version >/dev/null 2>&1; then
  echo "Bootstrapping pip inside .venv ..."
  "$VP" -m ensurepip --upgrade 2>/dev/null || {
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/code_agent_get_pip.py
    "$VP" /tmp/code_agent_get_pip.py --no-warn-script-location
    rm -f /tmp/code_agent_get_pip.py
  }
fi

"$VP" -m pip install --upgrade pip
"$VP" -m pip install -r requirements.txt

echo ""
echo "OK. Activate and run:"
echo "  source .venv/bin/activate"
echo "  python main.py YOUR-JIRA-KEY"
