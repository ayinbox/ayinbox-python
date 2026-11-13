from __future__ import annotations

import datetime as _dt
import json
import math
import re
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Mapping, Optional, Type

import httpx

__all__ = [
    "AyInboxError",
    "APIConnectionError",
    "APITimeoutError",
    "APIError",
    "ValidationError",
    "BadRequestError",
    "UnprocessableEntityError",
    "AuthenticationError",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "InternalServerError",
    "ServiceUnavailableError",
    "SignatureVerificationError",
]

_CODE_RE = re.compile(r"^[a-z0-9_]+$")

_DEFAULT_CODES: Dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    402: "insufficient_credits",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "unprocessable",
    429: "rate_limit_exceeded",
    500: "internal_error",
    501: "not_implemented",
    503: "service_unavailable",
}


class AyInboxError(Exception):
    """Base class for every error this library raises."""


class APIConnectionError(AyInboxError):
    """The request did not get an HTTP answer (DNS, TLS, refused or reset connection)."""


class APITimeoutError(APIConnectionError):
    """The request timed out."""


class SignatureVerificationError(AyInboxError):
    """A webhook signature did not verify."""


class APIError(AyInboxError):
    """The API answered with a non-2xx status."""

    status: int
    code: str
    message: str
    reason: Optional[str]
    request_id: Optional[str]
    body: Any
    headers: httpx.Headers
    retry_after: Optional[float]

    def __init__(
        self,
        *,
        status: int,
        code: str,
        message: str,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
        body: Any = None,
        headers: Optional[httpx.Headers] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        self.status = status
        self.code = code
        self.message = message
        self.reason = reason
        self.request_id = request_id
        self.body = body
        self.headers = headers if headers is not None else httpx.Headers()
        self.retry_after = retry_after
        text = f"{status} {code}: {message}"
        if request_id:
            text += f" (request_id: {request_id})"
        super().__init__(text)

    @property
    def status_code(self) -> int:
        return self.status


class ValidationError(APIError):
    """Parent of the 400 and 422 errors."""


class BadRequestError(ValidationError):
    pass


class UnprocessableEntityError(ValidationError):
    pass


class AuthenticationError(APIError):
    pass


class PaymentRequiredError(APIError):
    pass


class PermissionDeniedError(APIError):
    pass


class NotFoundError(APIError):
    pass


class ConflictError(APIError):
    pass


class RateLimitError(APIError):
    pass


class ServerError(APIError):
    """Parent of every 5xx error."""


class InternalServerError(ServerError):
    pass


class ServiceUnavailableError(ServerError):
    pass


_STATUS_CLASSES: Dict[int, Type[APIError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    503: ServiceUnavailableError,
}


def _error_class(status: int) -> Type[APIError]:
    cls = _STATUS_CLASSES.get(status)
    if cls is not None:
        return cls
    if status >= 500:
        return InternalServerError
    return APIError


def default_code(status: int) -> str:
    if status in _DEFAULT_CODES:
        return _DEFAULT_CODES[status]
    if status >= 500:
        return "internal_error"
    return "http_error"


def parse_retry_after(value: Optional[str]) -> Optional[float]:
    """Parse a Retry-After header given in seconds or as an HTTP date."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            when = parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            return None
        if when is None:
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=_dt.timezone.utc)
        seconds = (when - _dt.datetime.now(_dt.timezone.utc)).total_seconds()
    if math.isnan(seconds) or math.isinf(seconds):
        return None
    return max(0.0, seconds)


def _str_or_none(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value else None


def make_api_error(response: httpx.Response) -> APIError:
    """Build the typed error for a non-2xx response."""
    status = response.status_code
    text = response.text
    parsed: Any = None
    if text:
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = None
    body: Mapping[str, Any] = parsed if isinstance(parsed, dict) else {}

    code = _str_or_none(body.get("code"))
    if code is None:
        err = _str_or_none(body.get("error"))
        code = err if err is not None and _CODE_RE.match(err) else default_code(status)

    message = _str_or_none(body.get("message")) or _str_or_none(body.get("error"))
    if message is None:
        message = text.strip() if text and not body else (response.reason_phrase or "HTTP error")

    request_id = _str_or_none(body.get("request_id")) or _str_or_none(response.headers.get("x-request-id"))

    retry_after = parse_retry_after(response.headers.get("retry-after"))
    if retry_after is None:
        ra = body.get("retry_after")
        if isinstance(ra, (int, float)) and not isinstance(ra, bool):
            retry_after = float(ra)
    if retry_after is None:
        ra_ms = body.get("retry_after_ms")
        if isinstance(ra_ms, (int, float)) and not isinstance(ra_ms, bool):
            retry_after = float(math.ceil(ra_ms / 1000))

    cls = _error_class(status)
    return cls(
        status=status,
        code=code,
        message=message,
        reason=_str_or_none(body.get("reason")),
        request_id=request_id,
        body=parsed if parsed is not None else text,
        headers=response.headers,
        retry_after=retry_after,
    )
