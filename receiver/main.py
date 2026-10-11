#!/usr/bin/env python3
"""RayzHub Dedicated Message Receiving Outlet.

Fetches messages and received items strictly and exclusively via the BLAST URL
(Blast Gateway Proxy -> Supabase Backend). No direct local SQLite queries.
"""

import os
import sys
import json
import time
import socket
import shutil
import urllib.request
import urllib.parse
import urllib.error
import threading
import subprocess
import webbrowser
from http.server import HTTPServer, ThreadingHTTPServer, SimpleHTTPRequestHandler

# Base Directories
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RAYZHUB_DIR = os.path.dirname(CURRENT_DIR)
UPLOADS_DIR = os.path.join(RAYZHUB_DIR, "uploads")


def load_env():
    """Load configuration from .env file if available."""
    candidates = [
        os.path.join(RAYZHUB_DIR, ".env"),
        os.path.join(CURRENT_DIR, ".env"),
        ".env",
    ]
    for env_path in candidates:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception as e:
                sys.stderr.write(f"[-] Error loading {env_path}: {e}\n")


load_env()

# Configuration
BLAST_URL = (
    os.getenv("BLAST_URL")
    or "https://sas-the-treasure-grape-xr-prototype.onrender.com"
).rstrip("/")
BLAST_KEY = os.getenv("BLAST_KEY") or os.getenv("BLAST_API_KEY") or "blast-secret-key-1"
RECEIVER_PORT = int(os.getenv("RECEIVER_PORT") or "8001")
HOST = "0.0.0.0"


def get_blast_headers(custom: dict = None) -> dict:
    """Create authentication and telemetry headers for Blast Gateway."""
    headers = {
        "User-Agent": "RayzHub-DedicatedReceiver/2.0",
        "X-Blast-Key": BLAST_KEY,
        "Accept": "application/json",
    }
    if custom:
        headers.update(custom)
    return headers


def check_blast_status() -> dict:
    """Check connectivity and latency to the BLAST URL."""
    health_url = f"{BLAST_URL}/health"
    start_time = time.time()
    req = urllib.request.Request(health_url, headers=get_blast_headers(), method="GET")

    try:
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            raw = resp.read().decode("utf-8")
            try:
                data = json.loads(raw)
            except Exception:
                data = {"raw": raw}
            return {
                "healthy": True,
                "status": "online",
                "blast_url": BLAST_URL,
                "latency_ms": elapsed_ms,
                "gateway_info": data,
            }
    except Exception as exc:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "healthy": False,
            "status": "unreachable",
            "blast_url": BLAST_URL,
            "latency_ms": elapsed_ms,
            "error": str(exc),
        }


def fetch_from_blast_url(order: str = "id.desc", limit: int = 500, request_type: str = None) -> dict:
    """Fetch messages strictly and only via the BLAST URL Proxy.

    Routes:
        Receiver Outlet -> BLAST_URL/v1/proxy/rest/v1/requests -> Supabase
    """
    params = {
        "select": "*",
        "order": order or "id.desc",
    }
    if limit and limit > 0:
        params["limit"] = str(limit)
    if request_type and request_type != "all":
        params["request_type"] = f"eq.{request_type}"

    query_str = urllib.parse.urlencode(params)
    target_url = f"{BLAST_URL}/v1/proxy/rest/v1/requests?{query_str}"

    headers = get_blast_headers()

    last_err = None
    for attempt in range(2):
        start_time = time.time()
        req = urllib.request.Request(target_url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=14.0) as resp:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                raw = resp.read().decode("utf-8")
                data = json.loads(raw) if raw else []

                if isinstance(data, dict) and "error" in data:
                    return {
                        "success": False,
                        "error": data.get("error"),
                        "details": data.get("details"),
                        "blast_url": BLAST_URL,
                        "latency_ms": elapsed_ms,
                        "items": [],
                    }

                items = data if isinstance(data, list) else []
                return {
                    "success": True,
                    "source": "blast_url",
                    "blast_url": BLAST_URL,
                    "latency_ms": elapsed_ms,
                    "count": len(items),
                    "items": items,
                    "synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
        except urllib.error.HTTPError as he:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            err_body = he.read().decode("utf-8", errors="ignore")
            return {
                "success": False,
                "error": f"HTTP {he.code}",
                "details": err_body,
                "blast_url": BLAST_URL,
                "latency_ms": elapsed_ms,
                "items": [],
            }
        except Exception as exc:
            last_err = str(exc)
            time.sleep(0.5)

    return {
        "success": False,
        "error": "Connection Failed",
        "details": last_err or "Unknown error",
        "blast_url": BLAST_URL,
        "latency_ms": 0,
        "items": [],
    }


def transmit_test_via_blast(payload: dict) -> dict:
    """Send a test message or submission directly into the BLAST queue."""
    target_url = f"{BLAST_URL}/v1/queue/rest/v1/requests"
    headers = get_blast_headers({
        "Content-Type": "application/json",
        "X-Priority": "1",
        "X-Idempotency-Key": f"test-{int(time.time()*1000)}",
    })
    payload_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(target_url, data=payload_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {"status": "enqueued"}
    except Exception as exc:
        return {"error": str(exc)}


class ReceiverOutletHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler for RayzHub Dedicated Message Outlet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CURRENT_DIR, **kwargs)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Blast-Key")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Primary GUI Outlet Page
        if parsed.path in ("/", "/receiver", "/receiver.html", "/index.html"):
            for candidate in ("receiver.html", "index.html"):
                page_path = os.path.join(CURRENT_DIR, candidate)
                if os.path.exists(page_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-cache, must-revalidate")
                    self._send_cors_headers()
                    self.end_headers()
                    with open(page_path, "rb") as f:
                        self.wfile.write(f.read())
                    return
            self.send_error(404, "receiver.html not found")
            return

        # 2. API Endpoint: Fetch received messages strictly via BLAST URL
        if parsed.path == "/api/received":
            order = query.get("order", ["id.desc"])[0]
            limit = int(query.get("limit", [500])[0])
            req_type = query.get("type", ["all"])[0]

            result = fetch_from_blast_url(order=order, limit=limit, request_type=req_type)
            status_code = 200 if result.get("success") else 502

            resp_bytes = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 3. API Endpoint: BLAST Gateway Health & Latency Telemetry
        if parsed.path == "/api/status":
            status = check_blast_status()
            resp_bytes = json.dumps(status).encode("utf-8")
            self.send_response(200 if status.get("healthy") else 503)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 4. API Endpoint: Received Item Stats and Metrics (from Blast URL)
        if parsed.path == "/api/stats":
            result = fetch_from_blast_url(limit=1000)
            items = result.get("items", [])

            total = len(items)
            types_breakdown = {}
            tips_count = 0
            anonymous_count = 0
            latest_time = None

            for it in items:
                t = it.get("request_type") or "message"
                types_breakdown[t] = types_breakdown.get(t, 0) + 1
                if it.get("amount") or t == "tip":
                    tips_count += 1
                if it.get("is_anonymous") or it.get("name") == "Anonymous":
                    anonymous_count += 1
                if not latest_time and it.get("created_at"):
                    latest_time = it.get("created_at")

            stats = {
                "total_received": total,
                "types_breakdown": types_breakdown,
                "tips_count": tips_count,
                "anonymous_count": anonymous_count,
                "latest_activity": latest_time,
                "blast_url": BLAST_URL,
                "blast_latency_ms": result.get("latency_ms"),
                "blast_connected": result.get("success", False),
            }

            resp_bytes = json.dumps(stats).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 5. Static uploads media serving (e.g. proof images / attachments)
        if parsed.path.startswith("/uploads/"):
            rel_name = parsed.path.replace("/uploads/", "").lstrip("/")
            file_path = os.path.join(UPLOADS_DIR, rel_name)
            if os.path.isfile(file_path):
                content_type = "application/octet-stream"
                ext = os.path.splitext(file_path)[1].lower()
                if ext in (".jpg", ".jpeg"):
                    content_type = "image/jpeg"
                elif ext == ".png":
                    content_type = "image/png"
                elif ext == ".webp":
                    content_type = "image/webp"
                elif ext == ".gif":
                    content_type = "image/gif"

                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "public, max-age=86400")
                self._send_cors_headers()
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Uploaded asset not found")
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        # Transmit test submission via BLAST Gateway
        if parsed.path == "/api/transmit":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body) if body else {}

                result = transmit_test_via_blast(payload)
                resp_bytes = json.dumps(result).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(resp_bytes)
                return
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] ReceiverOutlet: {format % args}\n")


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


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


def main():
    port = RECEIVER_PORT
    url = f"http://127.0.0.1:{port}"

    if is_port_in_use(port):
        print(f"[!] Port {port} is already bound by an active instance.")
        print(f"[*] Opening Receiver Outlet at {url} (no localhost)...")
        open_browser(url)
        print(f"[+] Webpage opened: {url}")
        sys.exit(0)

    # Launch browser automatically
    def _open_when_ready():
        time.sleep(1.0)
        open_browser(url)

    threading.Thread(target=_open_when_ready, daemon=True).start()

    print("==================================================================")
    print(" RAYZHUB DEDICATED MESSAGE RECEIVING OUTLET")
    print(" Powered strictly and exclusively by BLAST URL")
    print("==================================================================")
    print(f"[*] Serving on:           {url}")
    print(f"[*] BLAST Fetch URL:      {BLAST_URL}")
    print(f"[*] Storage / DB Mode:    BLAST Proxy (Supabase Backend)")
    print("==================================================================")

    # Initial probe to verify BLAST URL connection
    probe = check_blast_status()
    if probe.get("healthy"):
        print(f"[+] BLAST Gateway Reachable! Latency: {probe.get('latency_ms')}ms")
    else:
        print(f"[!] Warning: BLAST Gateway returned error: {probe.get('error')}")

    print("==================================================================")

    server = ThreadingHTTPServer((HOST, port), ReceiverOutletHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping Receiver Outlet server.")
        server.server_close()


if __name__ == "__main__":
    main()
