from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Iterator, Mapping, Optional, Type

import httpx

from . import _async_resources as ar
from . import _resources as sr
from ._core import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    NOT_GIVEN,
    BaseClient,
    RequestOptions,
    TimeoutTypes,
)
from ._errors import APIConnectionError, APIError, APITimeoutError, AyInboxError, make_api_error
from ._pagination import AsyncPage, SyncPage

__all__ = ["AyInbox", "AsyncAyInbox"]


def _connection_error(exc: httpx.TransportError) -> APIConnectionError:
    if isinstance(exc, httpx.TimeoutException):
        return APITimeoutError(f"Request timed out ({type(exc).__name__}).")
    return APIConnectionError(f"Connection error ({type(exc).__name__}): {exc}")


class AyInbox(BaseClient):
    """Synchronous AY Inbox client.

    ``api_key`` falls back to ``AYINBOX_API_KEY`` and ``base_url`` to
    ``AYINBOX_BASE_URL`` (default ``https://api.ayinbox.com/v1``).
    """

    me: sr.Me
    campaigns: sr.Campaigns
    contacts: sr.Contacts
    mailboxes: sr.Mailboxes
    unibox: sr.Unibox
    templates: sr.Templates
    webhooks: sr.Webhooks
    analytics: sr.Analytics
    suppressions: sr.Suppressions
    ai_tools: sr.AiTools

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._owns_http = http_client is None
        self._http = http_client if http_client is not None else httpx.Client(timeout=timeout)
        self._sleep: Callable[[float], None] = time.sleep
        self.me = sr.Me(self)
        self.campaigns = sr.Campaigns(self)
        self.contacts = sr.Contacts(self)
        self.mailboxes = sr.Mailboxes(self)
        self.unibox = sr.Unibox(self)
        self.templates = sr.Templates(self)
        self.webhooks = sr.Webhooks(self)
        self.analytics = sr.Analytics(self)
        self.suppressions = sr.Suppressions(self)
        self.ai_tools = sr.AiTools(self)

    def close(self) -> None:
        """Close the underlying HTTP client if this instance created it."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> "AyInbox":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def _send(self, opts: RequestOptions) -> Any:
        attempt = 0
        while True:
            request = self._build_request(self._http, opts)
            try:
                response = self._http.send(request)
            except httpx.TransportError as exc:
                if self._should_retry_connection(opts, attempt):
                    self._sleep(self._retry_delay(attempt, None))
                    attempt += 1
                    continue
                raise _connection_error(exc) from exc
            if response.is_success:
                return self._parse_success(response)
            error = make_api_error(response)
            if self._should_retry_status(opts, attempt, error):
                self._sleep(self._retry_delay(attempt, error))
                attempt += 1
                continue
            raise error

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = NOT_GIVEN,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        safe_to_retry: bool = False,
    ) -> Any:
        return self._send(
            RequestOptions(
                method=method.upper(),
                path=path,
                query=dict(query or {}),
                body=body,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
                safe_to_retry=safe_to_retry,
            )
        )

    def _fetch_page(self, opts: RequestOptions) -> SyncPage[Any]:
        response = self._send(opts)
        if not isinstance(response, dict):
            raise AyInboxError(f"Expected a paginated JSON object from {opts.path}.")
        return SyncPage(self, response, opts)

    def _get_page(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = NOT_GIVEN,
        timeout: TimeoutTypes = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> SyncPage[Any]:
        return self._fetch_page(
            RequestOptions(
                method=method.upper(),
                path=path,
                query={k: v for k, v in (query or {}).items() if v is not None},
                body=body,
                timeout=timeout,
                extra_headers=extra_headers,
                safe_to_retry=True,
            )
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: TimeoutTypes = None,
    ) -> Any:
        """Call any route. ``path`` is relative to the base URL (``"/campaigns"``).

        Returns the decoded JSON, ``None`` for an empty body, or raw ``bytes`` for a
        non-JSON body. ``body=None`` sends no body. Same auth, retries and errors as
        every other method.
        """
        return self._request(
            method,
            path,
            query=query,
            body=NOT_GIVEN if body is None else body,
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=headers,
        )

    def paginate(
        self,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        method: str = "GET",
        body: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: TimeoutTypes = None,
    ) -> Iterator[Dict[str, Any]]:
        """Walk every page of a ``data`` + ``pagination`` list and yield its rows."""
        page = self._get_page(
            method,
            path,
            query=query,
            body=NOT_GIVEN if body is None else body,
            timeout=timeout,
            extra_headers=headers,
        )
        return page.auto_paging_iter()


class AsyncAyInbox(BaseClient):
    """Asynchronous AY Inbox client. Same surface as ``AyInbox``, every call awaited."""

    me: ar.AsyncMe
    campaigns: ar.AsyncCampaigns
    contacts: ar.AsyncContacts
    mailboxes: ar.AsyncMailboxes
    unibox: ar.AsyncUnibox
    templates: ar.AsyncTemplates
    webhooks: ar.AsyncWebhooks
    analytics: ar.AsyncAnalytics
    suppressions: ar.AsyncSuppressions
    ai_tools: ar.AsyncAiTools

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._owns_http = http_client is None
        self._http = http_client if http_client is not None else httpx.AsyncClient(timeout=timeout)
        self._sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
        self.me = ar.AsyncMe(self)
        self.campaigns = ar.AsyncCampaigns(self)
        self.contacts = ar.AsyncContacts(self)
        self.mailboxes = ar.AsyncMailboxes(self)
        self.unibox = ar.AsyncUnibox(self)
        self.templates = ar.AsyncTemplates(self)
        self.webhooks = ar.AsyncWebhooks(self)
        self.analytics = ar.AsyncAnalytics(self)
        self.suppressions = ar.AsyncSuppressions(self)
        self.ai_tools = ar.AsyncAiTools(self)

    async def close(self) -> None:
        """Close the underlying HTTP client if this instance created it."""
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> "AsyncAyInbox":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def _send(self, opts: RequestOptions) -> Any:
        attempt = 0
        while True:
            request = self._build_request(self._http, opts)
            try:
                response = await self._http.send(request)
            except httpx.TransportError as exc:
                if self._should_retry_connection(opts, attempt):
                    await self._sleep(self._retry_delay(attempt, None))
                    attempt += 1
                    continue
                raise _connection_error(exc) from exc
            if response.is_success:
                return self._parse_success(response)
            error: APIError = make_api_error(response)
            if self._should_retry_status(opts, attempt, error):
                await self._sleep(self._retry_delay(attempt, error))
                attempt += 1
                continue
            raise error

    async def _request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = NOT_GIVEN,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        safe_to_retry: bool = False,
    ) -> Any:
        return await self._send(
            RequestOptions(
                method=method.upper(),
                path=path,
                query=dict(query or {}),
                body=body,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
                safe_to_retry=safe_to_retry,
            )
        )

    async def _fetch_page(self, opts: RequestOptions) -> AsyncPage[Any]:
        response = await self._send(opts)
        if not isinstance(response, dict):
            raise AyInboxError(f"Expected a paginated JSON object from {opts.path}.")
        return AsyncPage(self, response, opts)

    async def _get_page(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = NOT_GIVEN,
        timeout: TimeoutTypes = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> AsyncPage[Any]:
        return await self._fetch_page(
            RequestOptions(
                method=method.upper(),
                path=path,
                query={k: v for k, v in (query or {}).items() if v is not None},
                body=body,
                timeout=timeout,
                extra_headers=extra_headers,
                safe_to_retry=True,
            )
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: TimeoutTypes = None,
    ) -> Any:
        """Call any route. See ``AyInbox.request``."""
        return await self._request(
            method,
            path,
            query=query,
            body=NOT_GIVEN if body is None else body,
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=headers,
        )

    async def paginate(
        self,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        method: str = "GET",
        body: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: TimeoutTypes = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Walk every page of a ``data`` + ``pagination`` list and yield its rows."""
        page = await self._get_page(
            method,
            path,
            query=query,
            body=NOT_GIVEN if body is None else body,
            timeout=timeout,
            extra_headers=headers,
        )
        async for row in page.auto_paging_iter():
            yield row
