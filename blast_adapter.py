"""Blast Gateway Integration Adapter for RayzHub.

Replaces direct Supabase credentials with secure, queued Blast Gateway routing:
    RayzHub -> Blast Gateway (Render / Local) -> Supabase
"""

import os
import uuid
import json
import logging
import requests
from typing import Any, Dict, List, Optional

logger = logging.getLogger("RayzHub-Blast")

# Load environment configuration
BLAST_URL = os.getenv("BLAST_URL", "http://127.0.0.1:8080").rstrip("/")
BLAST_API_KEY = os.getenv("BLAST_API_KEY", "blast-secret-key-1")
BLAST_QUEUE_ENABLED = os.getenv("BLAST_QUEUE_ENABLED", "true").lower() in ("true", "1", "yes")
BLAST_TIMEOUT = float(os.getenv("BLAST_TIMEOUT_SECONDS", "10.0"))


class BlastGatewayClient:
    """Client for routing database and queue operations through Blast Gateway."""

    def __init__(self, base_url: str = BLAST_URL, api_key: str = BLAST_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-Blast-Key": self.api_key,
            "User-Agent": "RayzHub-BlastAdapter/1.0",
        })

    def is_healthy(self) -> bool:
        """Check if Blast Gateway is reachable and operational."""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Fetch detailed status from Blast Gateway."""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                data["gateway_url"] = self.base_url
                data["connected"] = True
                return data
        except Exception as e:
            return {
                "connected": False,
                "gateway_url": self.base_url,
                "error": str(e)
            }
        return {"connected": False, "gateway_url": self.base_url}

    def enqueue(
        self,
        target_path: str,
        method: str = "POST",
        json_data: Optional[Any] = None,
        priority: int = 0,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enqueue an asynchronous request into Blast queue to be executed to Supabase."""
        url = f"{self.base_url}/v1/queue/{target_path.lstrip('/')}"
        headers = {
            "Content-Type": "application/json",
            "X-Priority": str(priority),
            "X-Idempotency-Key": idempotency_key or str(uuid.uuid4())
        }
        resp = self.session.request(
            method=method.upper(),
            url=url,
            json=json_data,
            headers=headers,
            timeout=BLAST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()

    def proxy(
        self,
        target_path: str,
        method: str = "GET",
        json_data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Synchronously forward a request through Blast security proxy directly to Supabase."""
        url = f"{self.base_url}/v1/proxy/{target_path.lstrip('/')}"
        resp = self.session.request(
            method=method.upper(),
            url=url,
            json=json_data,
            params=params,
            timeout=BLAST_TIMEOUT
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


# Singleton client
blast_client = BlastGatewayClient()


# ─── CONVENIENCE DISPATCHERS FOR RAYZHUB ───

def dispatch_request_to_blast(request_data: dict) -> Optional[dict]:
    """Forward a newly created user request / payment proof to Supabase via Blast."""
    clean_data = {
        "name": request_data.get("name"),
        "email": request_data.get("email"),
        "message": request_data.get("message"),
        "photo_path": request_data.get("photo_path"),
        "request_type": request_data.get("request_type", "request"),
        "amount": request_data.get("amount"),
        "transaction_id": request_data.get("transaction_id"),
        "is_anonymous": bool(request_data.get("is_anonymous", False)),
        "status": request_data.get("status", "pending"),
    }
    try:
        if BLAST_QUEUE_ENABLED:
            res = blast_client.enqueue(
                target_path="rest/v1/requests",
                method="POST",
                json_data=clean_data,
                priority=1,
                idempotency_key=f"req-{request_data.get('id', uuid.uuid4())}"
            )
            return {"queued": True, "job_id": res.get("job_id"), "via": "blast_queue"}
        else:
            res = blast_client.proxy(
                target_path="rest/v1/requests",
                method="POST",
                json_data=clean_data
            )
            return {"queued": False, "result": res, "via": "blast_proxy"}
    except Exception as e:
        logger.warning(f"Could not forward request to Blast gateway: {e}")
        return None


def dispatch_config_to_blast(config_key: str, config_data: dict) -> Optional[dict]:
    """Sync layout configuration to Supabase widget_configs table via Blast."""
    payload = {
        "config_key": config_key,
        "config_json": json.dumps(config_data) if isinstance(config_data, dict) else str(config_data)
    }
    try:
        if BLAST_QUEUE_ENABLED:
            res = blast_client.enqueue(
                target_path="rest/v1/widget_configs",
                method="POST",
                json_data=payload,
                priority=0,
                idempotency_key=f"cfg-{config_key}-{uuid.uuid4().hex[:6]}"
            )
            return {"queued": True, "job_id": res.get("job_id"), "via": "blast_queue"}
        else:
            res = blast_client.proxy(
                target_path="rest/v1/widget_configs",
                method="POST",
                json_data=payload
            )
            return {"queued": False, "result": res, "via": "blast_proxy"}
    except Exception as e:
        logger.warning(f"Could not sync configuration to Blast gateway: {e}")
        return None


def dispatch_link_to_blast(link_data: dict) -> Optional[dict]:
    """Sync short link to Supabase link_items table via Blast."""
    clean_data = {
        "title": link_data.get("title"),
        "target_url": link_data.get("target_url"),
        "short_code": link_data.get("short_code"),
        "clicks": link_data.get("clicks", 0)
    }
    try:
        if BLAST_QUEUE_ENABLED:
            res = blast_client.enqueue(
                target_path="rest/v1/link_items",
                method="POST",
                json_data=clean_data,
                idempotency_key=f"link-{clean_data.get('short_code')}"
            )
            return {"queued": True, "job_id": res.get("job_id"), "via": "blast_queue"}
        else:
            res = blast_client.proxy(
                target_path="rest/v1/link_items",
                method="POST",
                json_data=clean_data
            )
            return {"queued": False, "result": res, "via": "blast_proxy"}
    except Exception as e:
        logger.warning(f"Could not sync link to Blast gateway: {e}")
        return None


def dispatch_log_to_blast(log_data: dict) -> Optional[dict]:
    """Sync verification audit log to Supabase verification_logs table via Blast."""
    clean_data = {
        "user_id": log_data.get("user_id"),
        "action": log_data.get("action"),
        "ip_address": log_data.get("ip_address"),
        "status": log_data.get("status"),
        "details": log_data.get("details")
    }
    try:
        if BLAST_QUEUE_ENABLED:
            res = blast_client.enqueue(
                target_path="rest/v1/verification_logs",
                method="POST",
                json_data=clean_data,
                priority=-1
            )
            return {"queued": True, "job_id": res.get("job_id"), "via": "blast_queue"}
    except Exception as e:
        logger.warning(f"Could not sync audit log to Blast gateway: {e}")
        return None
