from __future__ import annotations

import asyncio
from typing import Any, Awaitable, List, TypeVar

import httpx
import pytest

import ayinbox
from ayinbox import AsyncPage

from .conftest import TEST_KEY, MockAPI, error_response, make_async_client

T = TypeVar("T")


def run(coro: Awaitable[T]) -> T:
    async def main() -> T:
        return await coro

    return asyncio.run(main())


def test_async_headers_and_me(api: MockAPI) -> None:
    async def go() -> Any:
        async with make_async_client(api, []) as c:
            return await c.me.get()

    me = run(go())
    assert me["organization_name"] == "Example Co"
    assert api.last.headers["authorization"] == f"Bearer {TEST_KEY}"
    assert api.last.headers["user-agent"].startswith("ayinbox-python/")


def test_async_pagination(api: MockAPI) -> None:
    async def go() -> List[str]:
        c = make_async_client(api, [])
        page = await c.campaigns.list()
        assert isinstance(page, AsyncPage)
        return [row["id"] async for row in page]

    assert len(run(go())) == 3
    assert api.requests[1].url.params["cursor"] == "c1_ZmFrZS1jdXJzb3ItcGFnZS0y"


def test_async_generic_paginate(api: MockAPI) -> None:
    async def go() -> int:
        c = make_async_client(api, [])
        return len([row async for row in c.paginate("/campaigns")])

    assert run(go()) == 3


def test_async_retry_and_no_retry(api: MockAPI) -> None:
    sleeps: List[float] = []

    async def go() -> None:
        c = make_async_client(api, sleeps)
        api.queue.append(error_response("429_api_key_rate_limited.json"))
        await c.contacts.get("22222222-2222-4222-8222-111111111111")
        api.queue.append(error_response("503_service_unavailable.json"))
        with pytest.raises(ayinbox.ServiceUnavailableError):
            await c.unibox.reply(email_account_id="m", to=["a@example.com"], subject="Hi")

    run(go())
    assert sleeps == [12.0]
    assert len(api.requests) == 3


def test_async_errors_and_bodies(api: MockAPI) -> None:
    async def go() -> None:
        c = make_async_client(api, [], max_retries=0)
        api.queue.append(error_response("404_not_found.json"))
        with pytest.raises(ayinbox.NotFoundError):
            await c.templates.get("x")
        await c.campaigns.delete("11111111-1111-4111-8111-111111111111")
        created = await c.contacts.create({"email": "lee@example.com"}, idempotency_key="k1")
        assert created[0]["email"] == "lee@example.com"
        assert api.last.headers["idempotency-key"] == "k1"
        api.queue.append(httpx.ConnectError("down"))
        with pytest.raises(ayinbox.APIConnectionError):
            await c.request("GET", "/me")

    run(go())


def test_async_resources_cover_every_sync_method() -> None:
    sync = ayinbox.AyInbox(TEST_KEY)
    asy = ayinbox.AsyncAyInbox(TEST_KEY)
    names = ["me", "campaigns", "contacts", "mailboxes", "unibox", "templates", "webhooks", "analytics",
             "suppressions", "ai_tools"]  # fmt: skip
    for name in names:
        s, a = getattr(sync, name), getattr(asy, name)
        public = [m for m in dir(s) if not m.startswith("_")]
        assert public == [m for m in dir(a) if not m.startswith("_")]
        for m in public:
            if m in ("steps", "leads"):
                continue
            attr = getattr(a, m)
            if callable(attr) and m not in ("verify_signature", "construct_event"):
                assert asyncio.iscoroutinefunction(attr), f"{name}.{m}"
    sync.close()
    run(asy.close())
