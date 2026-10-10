"""Blast Gateway Integration for RayzHub.

Routes all database mutations, requests, links, and widget configs through
the Blast clustering gateway (on Render or local cluster).

Architecture:
    RayzHub Client / Web App
               │
               ▼
    RayzHub FastAPI Server
               │
               ▼
    BLAST Gateway (Render: https://blast-gateway.onrender.com)
       ├── API Key Authentication & Rate Limiting
       ├── Request Sanitization & SQL Injection Firewall
       ├── Durable Queue & Retry Backoff Engine
       └── High-Performance Connection Pool
               │
               ▼
         Supabase Backend
"""

import os
import json
import time
import logging
import threading
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger("rayzhub.blast_gateway")


def load_env_file(filepath: str = ".env"):
    """Load key-value pairs from .env file into os.environ if not already set."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v
    except Exception as exc:
        logger.warning(f"Could not load .env file: {exc}")


# Auto-load .env
load_env_file()


class BlastGatewayClient:
    """Client for managing all Supabase operations via the Blast Render Gateway."""

    def __init__(
        self,
        blast_url: Optional[str] = None,
        blast_key: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout: float = 5.0,
    ):
        self.blast_url = (
            blast_url
            or os.getenv("BLAST_URL", "http://127.0.0.1:8080")
        ).rstrip("/")
        self.blast_key = (
            blast_key
            or os.getenv("BLAST_KEY", "blast-secret-key-1")
        )
        if enabled is None:
            self.enabled = os.getenv("ENABLE_BLAST_SYNC", "true").lower() in ("1", "true", "yes")
        else:
            self.enabled = enabled
        self.timeout = timeout
        self._executor_lock = threading.Lock()

    def _make_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "RayzHub-Client/2.0",
            "X-Blast-Key": self.blast_key,
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def check_health(self) -> Dict[str, Any]:
        """Check connection health and latency to Blast Gateway."""
        if not self.enabled:
            return {"status": "disabled", "url": self.blast_url, "healthy": False}

        url = f"{self.blast_url}/health"
        req = urllib.request.Request(url, headers=self._make_headers(), method="GET")
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = round((time.time() - start) * 1000, 2)
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "status": "connected",
                    "healthy": True,
                    "blast_url": self.blast_url,
                    "latency_ms": elapsed_ms,
                    "blast_status": data,
                }
        except Exception as exc:
            return {
                "status": "unreachable",
                "healthy": False,
                "blast_url": self.blast_url,
                "error": str(exc),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Fetch queue depth and cluster stats from Blast Gateway."""
        if not self.enabled:
            return {"status": "disabled"}

        url = f"{self.blast_url}/v1/queue/stats"
        req = urllib.request.Request(url, headers=self._make_headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return {"error": str(exc)}

    def queue_write(
        self,
        table: str,
        data: Any,
        method: str = "POST",
        idempotency_key: Optional[str] = None,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """
        Enqueue an asynchronous write to Supabase via Blast:
        POST /v1/queue/rest/v1/{table}
        """
        if not self.enabled:
            return {"status": "skipped", "reason": "Blast sync disabled"}

        url = f"{self.blast_url}/v1/queue/rest/v1/{table}"
        custom_headers = {
            "Prefer": "return=representation",
        }
        if idempotency_key:
            custom_headers["X-Idempotency-Key"] = idempotency_key
        if priority:
            custom_headers["X-Priority"] = str(priority)

        payload_bytes = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload_bytes,
            headers=self._make_headers(custom_headers),
            method=method.upper(),
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {"status": "queued"}
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            logger.error(f"Blast Queue HTTP {he.code}: {err_body}")
            return {"status": "error", "code": he.code, "details": err_body}
        except Exception as exc:
            logger.error(f"Blast Queue network error: {exc}")
            return {"status": "error", "details": str(exc)}

    def async_queue_write(
        self,
        table: str,
        data: Any,
        method: str = "POST",
        idempotency_key: Optional[str] = None,
        priority: int = 0,
    ):
        """Fire-and-forget non-blocking background queue submission."""
        threading.Thread(
            target=self.queue_write,
            args=(table, data, method, idempotency_key, priority),
            daemon=True,
        ).start()

    def proxy_read(
        self,
        table: str,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronously query Supabase through Blast Proxy:
        GET /v1/proxy/rest/v1/{table}?select=*
        """
        if not self.enabled:
            return {"error": "Blast sync disabled"}

        query_str = ""
        if params:
            query_str = "?" + urllib.parse.urlencode(params)
        url = f"{self.blast_url}/v1/proxy/rest/v1/{table}{query_str}"

        req = urllib.request.Request(
            url,
            headers=self._make_headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            logger.error(f"Blast Proxy read error: {exc}")
            return {"error": str(exc)}

    # ── High-Level RayzHub Table Operations ──

    def sync_request(self, request_data: Dict[str, Any]):
        """Queue a user request or crypto tip proof to Supabase."""
        idem = f"req-{request_data.get('id', int(time.time()*1000))}"
        self.async_queue_write("requests", request_data, idempotency_key=idem, priority=1)

    def sync_widget_config(self, config_key: str, config_dict: Dict[str, Any]):
        """Queue layout and widget updates to Supabase."""
        data = {
            "config_key": config_key,
            "config_json": json.dumps(config_dict),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        idem = f"cfg-{config_key}-{int(time.time())}"
        self.async_queue_write("widget_configs", data, idempotency_key=idem, priority=2)

    def sync_link(self, link_data: Dict[str, Any]):
        """Queue short links to Supabase."""
        idem = f"link-{link_data.get('short_code', int(time.time()))}"
        self.async_queue_write("link_items", link_data, idempotency_key=idem)

    def sync_click(self, short_code: str, clicks: int):
        """Queue link click count increment."""
        data = {"clicks": clicks}
        self.async_queue_write("link_items", data, method="PATCH", idempotency_key=f"click-{short_code}-{clicks}")

    def sync_verification_log(self, log_data: Dict[str, Any]):
        """Queue audit log event to Supabase."""
        self.async_queue_write("verification_logs", log_data, priority=0)

    def sync_user(self, user_data: Dict[str, Any]):
        """Queue user registration record to Supabase."""
        idem = f"user-{user_data.get('email', '')}"
        self.async_queue_write("users", user_data, idempotency_key=idem, priority=2)


# Global singleton instance
gateway = BlastGatewayClient()
