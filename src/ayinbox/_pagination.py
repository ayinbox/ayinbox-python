from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, Generic, Iterator, List, Mapping, Optional, TypeVar, cast

from ._core import RequestOptions
from ._errors import AyInboxError

if TYPE_CHECKING:
    from ._client import AsyncAyInbox, AyInbox

T = TypeVar("T")

__all__ = ["SyncPage", "AsyncPage"]


class _BasePage(Generic[T]):
    """One page of a ``data`` + ``pagination`` list.

    ``data`` holds this page's rows, ``next_cursor``/``has_more``/``total`` come from
    ``pagination``, and ``raw`` is the whole response (``counts`` and ``lead_counts``
    on a contact search live there).
    """

    data: List[T]
    next_cursor: Optional[str]
    has_more: bool
    total: Optional[int]
    raw: Dict[str, Any]

    def __init__(self, response: Mapping[str, Any], options: RequestOptions) -> None:
        self.raw = dict(response)
        self._options = options
        rows = response.get("data")
        self.data = cast(List[T], list(rows)) if isinstance(rows, list) else []
        pagination = response.get("pagination")
        pag: Mapping[str, Any] = pagination if isinstance(pagination, dict) else {}
        cursor = pag.get("next_cursor")
        self.next_cursor = cursor if isinstance(cursor, str) and cursor else None
        self.has_more = pag.get("has_more") is True
        total = pag.get("total")
        self.total = total if isinstance(total, int) and not isinstance(total, bool) else None

    def has_next_page(self) -> bool:
        return self.has_more and self.next_cursor is not None

    def _next_options(self) -> RequestOptions:
        if self.next_cursor is None or not self.has_more:
            raise AyInboxError("There is no next page.")
        return self._options.with_cursor(self.next_cursor)

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(rows={len(self.data)}, has_more={self.has_more}, next_cursor={self.next_cursor!r})"
        )


class SyncPage(_BasePage[T]):
    """A page from the sync client. Iterating it walks every page."""

    def __init__(self, client: "AyInbox", response: Mapping[str, Any], options: RequestOptions) -> None:
        super().__init__(response, options)
        self._client = client

    def get_next_page(self) -> "SyncPage[T]":
        return cast("SyncPage[T]", self._client._fetch_page(self._next_options()))

    def iter_pages(self) -> Iterator["SyncPage[T]"]:
        page: SyncPage[T] = self
        while True:
            yield page
            if not page.has_next_page():
                return
            page = page.get_next_page()

    def auto_paging_iter(self) -> Iterator[T]:
        for page in self.iter_pages():
            yield from page.data

    def __iter__(self) -> Iterator[T]:
        return self.auto_paging_iter()


class AsyncPage(_BasePage[T]):
    """A page from the async client. ``async for`` over it walks every page."""

    def __init__(self, client: "AsyncAyInbox", response: Mapping[str, Any], options: RequestOptions) -> None:
        super().__init__(response, options)
        self._client = client

    async def get_next_page(self) -> "AsyncPage[T]":
        return cast("AsyncPage[T]", await self._client._fetch_page(self._next_options()))

    async def iter_pages(self) -> AsyncIterator["AsyncPage[T]"]:
        page: AsyncPage[T] = self
        while True:
            yield page
            if not page.has_next_page():
                return
            page = await page.get_next_page()

    async def auto_paging_iter(self) -> AsyncIterator[T]:
        async for page in self.iter_pages():
            for row in page.data:
                yield row

    def __aiter__(self) -> AsyncIterator[T]:
        return self.auto_paging_iter()
