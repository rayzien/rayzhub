#!/usr/bin/env bash
# ==============================================================================
# RayzHub Dedicated Message Receiving Outlet Launcher
# Strictly powered by BLAST Gateway Proxy
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo " Starting RayzHub Dedicated Message Receiving Outlet"
echo " (Strictly fetching via BLAST URL)"
echo "=================================================================="

# Detect Python
if [ -f "../.venv/bin/python" ]; then
    PYTHON_BIN="../.venv/bin/python"
elif [ -f "../../BLAST/.venv/bin/python" ]; then
    PYTHON_BIN="../../BLAST/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "[-] Error: Python 3 not found."
    exit 1
fi

PORT="${RECEIVER_PORT:-8001}"
URL="http://127.0.0.1:${PORT}"

# If port is already active, launch browser and exit
if ss -tulpn 2>/dev/null | grep -q ":${PORT} " || (command -v nc >/dev/null 2>&1 && nc -z 127.0.0.1 "${PORT}" 2>/dev/null); then
    echo "[!] Port ${PORT} already active."
    echo "[*] Opening Receiver Outlet at ${URL} (no localhost)..."
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "${URL}" >/dev/null 2>&1 &
    fi
    $PYTHON_BIN -c "import webbrowser; webbrowser.open('${URL}')" 2>/dev/null || true
    echo "[+] Webpage opened: ${URL}"
    exit 0
fi

echo "[*] Starting Receiver Outlet on ${URL} ..."
exec $PYTHON_BIN main.py
