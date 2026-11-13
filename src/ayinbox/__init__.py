"""Official Python client for the AY Inbox REST API."""

from . import types, webhooks
from ._client import AsyncAyInbox, AyInbox
from ._core import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT
from ._errors import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    AyInboxError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
    SignatureVerificationError,
    UnprocessableEntityError,
    ValidationError,
)
from ._pagination import AsyncPage, SyncPage
from ._version import __version__
from .webhooks import construct_event, verify_signature

__all__ = [
    "__version__",
    "AyInbox",
    "AsyncAyInbox",
    "SyncPage",
    "AsyncPage",
    "DEFAULT_BASE_URL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
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
    "verify_signature",
    "construct_event",
    "types",
    "webhooks",
]
