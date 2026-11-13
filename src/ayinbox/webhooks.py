"""Webhook signature verification.

AY Inbox signs every delivery with ``X-Ayinbox-Signature: t=<unix-seconds>,v1=<hex>``,
an HMAC-SHA256 over ``<t>.<raw body>`` keyed with the endpoint secret (``whsec_...``,
prefix included). Always verify the raw request bytes, before any JSON parsing.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import List, Optional, Tuple, Union, cast

from ._errors import SignatureVerificationError
from .types import WebhookEvent

__all__ = [
    "SIGNATURE_HEADER",
    "EVENT_HEADER",
    "EVENT_ID_HEADER",
    "DEFAULT_TOLERANCE",
    "compute_signature",
    "verify_signature",
    "construct_event",
]

SIGNATURE_HEADER = "X-Ayinbox-Signature"
EVENT_HEADER = "X-Ayinbox-Event"
EVENT_ID_HEADER = "X-Ayinbox-Event-Id"
DEFAULT_TOLERANCE = 300

Payload = Union[bytes, bytearray, str]


def _as_bytes(payload: Payload) -> bytes:
    if isinstance(payload, str):
        return payload.encode("utf-8")
    return bytes(payload)


def compute_signature(payload: Payload, secret: str, timestamp: int) -> str:
    """Return the lowercase hex ``v1`` signature for a payload and timestamp."""
    message = str(int(timestamp)).encode("ascii") + b"." + _as_bytes(payload)
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _parse_header(header: str) -> Tuple[Optional[int], List[str]]:
    timestamp: Optional[int] = None
    signatures: List[str] = []
    for part in header.split(","):
        key, sep, value = part.strip().partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                return None, []
        elif key == "v1" and value:
            signatures.append(value)
    return timestamp, signatures


def _check(payload: Payload, header: str, secret: str, tolerance: float, now: Optional[float]) -> None:
    if not isinstance(header, str) or not header:
        raise SignatureVerificationError("Missing signature header.")
    if not secret:
        raise SignatureVerificationError("Missing webhook secret.")
    timestamp, signatures = _parse_header(header)
    if timestamp is None:
        raise SignatureVerificationError("Signature header has no valid timestamp.")
    if not signatures:
        raise SignatureVerificationError("Signature header has no v1 signature.")
    current = time.time() if now is None else now
    if abs(current - timestamp) > tolerance:
        raise SignatureVerificationError("Signature timestamp is outside the tolerance window.")
    expected = compute_signature(payload, secret, timestamp)
    matched = False
    for candidate in signatures:
        if hmac.compare_digest(expected.encode("ascii"), candidate.encode("utf-8", "replace")):
            matched = True
    if not matched:
        raise SignatureVerificationError("No signature matches the payload.")


def verify_signature(
    payload: Payload,
    header: str,
    secret: str,
    *,
    tolerance: float = DEFAULT_TOLERANCE,
    now: Optional[float] = None,
) -> bool:
    """Return True when ``header`` is a valid signature of ``payload`` for ``secret``.

    ``payload`` is the raw request body. ``tolerance`` is the allowed clock skew in
    seconds (default 300). ``now`` overrides the current Unix time, for tests.
    """
    try:
        _check(payload, header, secret, tolerance, now)
    except SignatureVerificationError:
        return False
    return True


def construct_event(
    payload: Payload,
    header: str,
    secret: str,
    *,
    tolerance: float = DEFAULT_TOLERANCE,
    now: Optional[float] = None,
) -> WebhookEvent:
    """Verify the signature, then parse the payload.

    Raises ``SignatureVerificationError`` when the signature does not verify or
    the body is not a JSON object.
    """
    _check(payload, header, secret, tolerance, now)
    try:
        event = json.loads(_as_bytes(payload).decode("utf-8"))
    except ValueError as exc:
        raise SignatureVerificationError("Payload is not valid JSON.") from exc
    if not isinstance(event, dict):
        raise SignatureVerificationError("Payload is not a JSON object.")
    return cast(WebhookEvent, event)
