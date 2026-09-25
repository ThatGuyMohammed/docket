"""Outgoing webhooks.

Each delivery carries an X-Docket-Signature header: hex HMAC-SHA256 of
"<timestamp>.<body>" with the shared WEBHOOK_SECRET.
"""

import hashlib
import hmac
import json
import logging
import time

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import WebhookEndpoint

log = logging.getLogger(__name__)


def sign_payload(secret: str, timestamp: int, body: bytes) -> str:
    msg = str(timestamp).encode() + b"." + body
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def deliver(db: Session, owner_id: int, event: str, payload: dict) -> int:
    endpoints = db.scalars(
        select(WebhookEndpoint).where(WebhookEndpoint.owner_id == owner_id)
    ).all()
    body = json.dumps({"event": event, "data": payload}, separators=(",", ":")).encode()
    ts = int(time.time())
    sig = sign_payload(get_settings().webhook_secret, ts, body)
    sent = 0
    for ep in endpoints:
        if event not in ep.events.split(","):
            continue
        try:
            httpx.post(
                ep.url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Docket-Timestamp": str(ts),
                    "X-Docket-Signature": sig,
                },
                timeout=5.0,
            )
            sent += 1
        except httpx.HTTPError as exc:
            log.warning("webhook to %s failed: %s", ep.url, exc)
    return sent
