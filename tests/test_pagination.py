from __future__ import annotations

import json
from typing import List

import httpx

from ayinbox import AyInbox

from .conftest import MockAPI, error_response


def test_walks_two_pages(api: MockAPI, client: AyInbox) -> None:
    page = client.campaigns.list(limit=2)
    assert len(page.data) == 2
    assert page.has_more and page.next_cursor == "c1_ZmFrZS1jdXJzb3ItcGFnZS0y"
    assert page.total == 3

    names = [c["name"] for c in page]
    assert len(names) == 3
    assert len(api.requests) == 2
    first, second = api.requests
    assert "cursor" not in first.url.params
    assert second.url.params["cursor"] == "c1_ZmFrZS1jdXJzb3ItcGFnZS0y"
    assert second.url.params["limit"] == "2"


def test_iter_pages_and_get_next_page(client: AyInbox) -> None:
    page = client.campaigns.list()
    nxt = page.get_next_page()
    assert not nxt.has_next_page()
    assert [len(p.data) for p in page.iter_pages()] == [2, 1]


def test_contact_search_resends_the_same_body(api: MockAPI, client: AyInbox) -> None:
    def first(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [{"id": "a"}],
                "pagination": {"next_cursor": "o1_next", "has_more": True, "total": 2},
                "counts": {"all": 2},
            },
        )

    def second(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"id": "b"}], "pagination": {"next_cursor": None, "has_more": False}})

    api.queue.extend([first, second])
    page = client.contacts.list(query="lee", sort_by="email", reverse=True)
    assert page.raw["counts"] == {"all": 2}
    assert [c["id"] for c in page.auto_paging_iter()] == ["a", "b"]
    bodies = [json.loads(r.content) for r in api.requests]
    assert bodies[0] == bodies[1] == {"query": "lee", "sort_by": "email", "reverse": True}
    assert api.requests[1].url.params["cursor"] == "o1_next"


def test_stops_when_cursor_missing_even_if_has_more(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(httpx.Response(200, json={"data": [{"id": "a"}], "pagination": {"has_more": True}}))
    assert [s["id"] for s in client.suppressions.list()] == ["a"]
    assert len(api.requests) == 1


def test_429_mid_walk_is_waited_out(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    page = client.campaigns.list()
    api.queue.append(error_response("429_api_key_rate_limited.json"))
    assert len(list(page)) == 3
    assert sleeps == [12.0]


def test_suppressions_last_page_shape(client: AyInbox) -> None:
    page = client.suppressions.list()
    assert page.next_cursor is None and page.has_more is False and page.total is None
    assert page.data[0]["kind"] == "email"
