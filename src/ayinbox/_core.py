from __future__ import annotations

import datetime as _dt
import json
import os
import random
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, Union
from urllib.parse import quote

import httpx

from ._errors import APIError, AyInboxError
from ._version import __version__

DEFAULT_BASE_URL = "https://api.ayinbox.com/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2

RETRYABLE_STATUSES = frozenset({429, 502, 503, 504})
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
MAX_RETRY_AFTER = 120.0
BACKOFF_BASE = 0.5
BACKOFF_CAP = 8.0

USER_AGENT = f"ayinbox-python/{__version__}"


class _NotGiven:
    """Marks an argument that was not passed (distinct from ``None``, which is JSON null)."""

    _instance: Optional["_NotGiven"] = None

    def __new__(cls) -> "_NotGiven":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN: Any = _NotGiven()

TimeoutTypes = Union[float, httpx.Timeout, None]


def path_param(value: Any) -> str:
    text = str(value)
    if not text:
        raise ValueError("A path parameter cannot be empty.")
    return quote(text, safe="")


def _rfc3339(value: Union[_dt.datetime, _dt.date]) -> str:
    if isinstance(value, _dt.datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=_dt.timezone.utc)
        text = value.astimezone(_dt.timezone.utc).isoformat()
        return text.replace("+00:00", "Z")
    return value.isoformat()


def _json_default(value: Any) -> Any:
    if isinstance(value, (_dt.datetime, _dt.date)):
        return _rfc3339(value)
    if isinstance(value, (set, frozenset, tuple)):
        return list(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def encode_json(body: Any) -> bytes:
    return json.dumps(body, default=_json_default, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _query_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (_dt.datetime, _dt.date)):
        return _rfc3339(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        return ",".join(_query_value(v) for v in value)
    return str(value)


def encode_query(query: Optional[Mapping[str, Any]]) -> List[Tuple[str, str]]:
    """Each parameter once; lists are comma-joined (the API refuses repeated parameters)."""
    if not query:
        return []
    out: List[Tuple[str, str]] = []
    for key, value in query.items():
        if value is None or value is NOT_GIVEN:
            continue
        out.append((key, _query_value(value)))
    return out


def validate_idempotency_key(key: str) -> None:
    if not isinstance(key, str) or not 1 <= len(key) <= 255 or any(not 33 <= ord(ch) <= 126 for ch in key):
        raise ValueError("An idempotency key is 1 to 255 visible ASCII characters.")


def redact(key: str) -> str:
    return f"{key[:6]}..." if len(key) > 10 else "***"


@dataclass(frozen=True)
class RequestOptions:
    method: str
    path: str
    query: Dict[str, Any] = field(default_factory=dict)
    body: Any = NOT_GIVEN
    idempotency_key: Optional[str] = None
    timeout: TimeoutTypes = None
    extra_headers: Optional[Mapping[str, str]] = None
    safe_to_retry: bool = False

    def with_cursor(self, cursor: str) -> "RequestOptions":
        query = dict(self.query)
        query["cursor"] = cursor
        return replace(self, query=query)


class BaseClient:
    base_url: str
    timeout: TimeoutTypes
    max_retries: int

    def __init__(
        self,
        *,
        api_key: Optional[str],
        base_url: Optional[str],
        timeout: TimeoutTypes,
        max_retries: int,
        default_headers: Optional[Mapping[str, str]],
    ) -> None:
        key = api_key if api_key is not None else os.environ.get("AYINBOX_API_KEY")
        if not key:
            raise AyInboxError("No API key: pass api_key or set the AYINBOX_API_KEY environment variable.")
        self._api_key = key
        url = base_url or os.environ.get("AYINBOX_BASE_URL") or DEFAULT_BASE_URL
        self.base_url = url.rstrip("/")
        if max_retries < 0:
            raise ValueError("max_retries must be 0 or more.")
        self.timeout = timeout
        self.max_retries = max_retries
        self._default_headers = dict(default_headers or {})
        self._random: Callable[[], float] = random.random

    def __repr__(self) -> str:
        return f"{type(self).__name__}(base_url={self.base_url!r}, api_key={redact(self._api_key)!r})"

    def _build_request(self, http: Union[httpx.Client, httpx.AsyncClient], opts: RequestOptions) -> httpx.Request:
        headers = httpx.Headers(
            {
                "Authorization": f"Bearer {self._api_key}",
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            }
        )
        for name, value in self._default_headers.items():
            headers[name] = value
        if opts.extra_headers:
            for name, value in opts.extra_headers.items():
                headers[name] = value
        content: Optional[bytes] = None
        if opts.body is not NOT_GIVEN:
            content = encode_json(opts.body)
            headers["Content-Type"] = "application/json"
        if opts.idempotency_key is not None:
            validate_idempotency_key(opts.idempotency_key)
            headers["Idempotency-Key"] = opts.idempotency_key
        url = f"{self.base_url}/{opts.path.lstrip('/')}"
        timeout = opts.timeout if opts.timeout is not None else self.timeout
        return http.build_request(
            opts.method,
            url,
            params=tuple(encode_query(opts.query)),
            content=content,
            headers=headers,
            timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
        )

    def _can_retry_unsafe(self, opts: RequestOptions) -> bool:
        return opts.method.upper() in _SAFE_METHODS or opts.safe_to_retry or opts.idempotency_key is not None

    def _should_retry_status(self, opts: RequestOptions, attempt: int, error: APIError) -> bool:
        if attempt >= self.max_retries or error.status not in RETRYABLE_STATUSES:
            return False
        if error.status == 429:
            return True  # a 429 never ran the request
        return self._can_retry_unsafe(opts)

    def _should_retry_connection(self, opts: RequestOptions, attempt: int) -> bool:
        return attempt < self.max_retries and self._can_retry_unsafe(opts)

    def _retry_delay(self, attempt: int, error: Optional[APIError]) -> float:
        if error is not None and error.retry_after is not None:
            return min(max(error.retry_after, 0.0), MAX_RETRY_AFTER)
        ceiling = min(BACKOFF_CAP, BACKOFF_BASE * (2.0**attempt))
        return self._random() * ceiling

    @staticmethod
    def _parse_success(response: httpx.Response) -> Any:
        content = response.content
        if not content or not content.strip():
            return None
        try:
            return json.loads(content)
        except ValueError:
            return content
