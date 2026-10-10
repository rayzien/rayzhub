#!/usr/bin/env bash
import os
import sys
import json
import sqlite3
import shutil
import socket
import threading
import time
import subprocess
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Determine base paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

# Locate SQLite database
DB_CANDIDATES = [
    os.path.join(PARENT_DIR, "requests.db"),
    os.path.join(CURRENT_DIR, "requests.db"),
    "requests.db",
]

def get_db_path():
    for p in DB_CANDIDATES:
        if os.path.exists(p):
            return p
    return os.path.join(PARENT_DIR, "requests.db")

def open_browser(url: str):
    """Open the webpage in the default browser using 127.0.0.1 (no localhost)."""
    try:
        webbrowser.open(url)
    except Exception:
        pass
    if shutil.which("xdg-open"):
        try:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def fetch_received_messages():
    """Fetch messages directly from SQLite database."""
    db_file = get_db_path()
    if not os.path.exists(db_file):
        return []
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, email, message, photo_path, request_type, amount, transaction_id, is_anonymous, created_at, status
            FROM requests
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        messages = [dict(row) for row in rows]
        conn.close()
        return messages
    except Exception as exc:
        print(f"[-] Error querying DB: {exc}")
        return []

class ReceiveRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler for RayzHub Receiver."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CURRENT_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path in ("/", "/receive", "/receive.html"):
            html_path = os.path.join(CURRENT_DIR, "receive.html")
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(html_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "receive.html not found")
                return

        elif parsed.path == "/api/received":
            messages = fetch_received_messages()
            response_data = json.dumps(messages).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(response_data)
            return

        elif parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "online", "service": "RayzHub Receiver"}).encode("utf-8"))
            return

        return super().do_GET()

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] Receiver: {format % args}\n")

def main():
    PORT = int(os.getenv("RECEIVE_PORT", "8001"))
    URL = f"http://127.0.0.1:{PORT}"

    # Handle port already in use: just open the webpage using link styled 127.0.0.1
    if is_port_in_use(PORT):
        print(f"[!] Address already in use on port {PORT}.")
        print(f"[*] Opening webpage at {URL} (no localhost)...")
        open_browser(URL)
        print(f"[+] Webpage opened: {URL}")
        sys.exit(0)

    # Launch browser automatically when server starts
    def _open_when_ready():
        time.sleep(1.0)
        open_browser(URL)

    threading.Thread(target=_open_when_ready, daemon=True).start()

    print("==========================================================")
    print(" RayzHub Receiver Service (Powered by BLAST Pipeline)")
    print("==========================================================")
    print(f"[*] Serving receive.html on {URL} ...")
    print(f"[*] DB Connection: {get_db_path()}")
    print("==========================================================")

    server = HTTPServer(("0.0.0.0", PORT), ReceiveRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping Receiver server.")
        server.server_close()

if __name__ == "__main__":
    main()
