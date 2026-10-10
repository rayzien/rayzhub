#!/usr/bin/env bash
# ==============================================================================
# RayzHub Runner Script (Powered by BLAST Gateway)
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")"

echo "=========================================================="
echo " Starting RayzHub Platform with BLAST Gateway"
echo "=========================================================="

# Check Python environment
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -f "../BLAST/.venv/bin/python" ]; then
    PYTHON_BIN="../BLAST/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "[-] Error: Python 3 not found."
    exit 1
fi

echo "[*] Using Python: $PYTHON_BIN"

# Check BLAST Gateway connectivity
echo "[*] Verifying BLAST Gateway status..."
$PYTHON_BIN verify_backups.py || true

PORT="${PORT:-8000}"
URL="http://127.0.0.1:${PORT}"

# If address is already in use, open the webpage using link styled 127.0.0.1 (no localhost)
if ss -tulpn 2>/dev/null | grep -q ":${PORT} " || lsof -i :"${PORT}" >/dev/null 2>&1 || (command -v nc >/dev/null 2>&1 && nc -z 127.0.0.1 "${PORT}" 2>/dev/null); then
    echo ""
    echo "[!] Address already in use on port ${PORT}."
    echo "[*] Opening webpage at ${URL} (no localhost)..."
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "${URL}" >/dev/null 2>&1 &
    fi
    $PYTHON_BIN -c "import webbrowser; webbrowser.open('${URL}')" 2>/dev/null || true
    echo "[+] Webpage opened: ${URL}"
    exit 0
fi

echo ""
echo "[*] Starting RayzHub API & Web Server on ${URL} ..."
exec $PYTHON_BIN main.py
