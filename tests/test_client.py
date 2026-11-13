from __future__ import annotations

import datetime as dt
import json

import httpx
import pytest

import ayinbox
from ayinbox import AyInbox, AyInboxError

from .conftest import TEST_KEY, MockAPI


def test_sends_auth_user_agent_and_accept(api: MockAPI, client: AyInbox) -> None:
    client.me.get()
    req = api.last
    assert str(req.url) == "https://api.ayinbox.com/v1/me"
    assert req.headers["authorization"] == f"Bearer {TEST_KEY}"
    assert req.headers["user-agent"] == f"ayinbox-python/{ayinbox.__version__}"
    assert req.headers["accept"] == "application/json"
    assert "idempotency-key" not in req.headers
    assert req.headers.get_list("authorization") == [f"Bearer {TEST_KEY}"]


def test_extra_headers_replace_rather_than_repeat(api: MockAPI, client: AyInbox) -> None:
    client.me.get(extra_headers={"X-Request-Id": "trace-1", "authorization": "Bearer other"})
    assert api.last.headers["x-request-id"] == "trace-1"
    assert api.last.headers.get_list("authorization") == ["Bearer other"]


def test_key_and_base_url_from_environment(monkeypatch: pytest.MonkeyPatch, api: MockAPI) -> None:
    monkeypatch.setenv("AYINBOX_API_KEY", "aybox_from_env_" + "x" * 30)
    monkeypatch.setenv("AYINBOX_BASE_URL", "https://example.test/v1/")
    c = AyInbox(http_client=httpx.Client(transport=httpx.MockTransport(api.handler)))
    assert c.base_url == "https://example.test/v1"
    c.me.get()
    assert str(api.last.url) == "https://example.test/v1/me"
    assert api.last.headers["authorization"].startswith("Bearer aybox_from_env_")


def test_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AYINBOX_API_KEY", raising=False)
    with pytest.raises(AyInboxError, match="AYINBOX_API_KEY"):
        AyInbox()


def test_repr_never_shows_the_key() -> None:
    c = AyInbox(TEST_KEY)
    assert TEST_KEY not in repr(c)
    assert "aybox_..." in repr(c)
    c.close()


def test_key_not_in_error_message(api: MockAPI, client: AyInbox) -> None:
    from .conftest import error_response

    api.queue.append(error_response("401_unauthorized.json"))
    with pytest.raises(ayinbox.AuthenticationError) as info:
        client.me.get()
    assert TEST_KEY not in str(info.value)
    assert TEST_KEY not in repr(info.value)


def test_generic_request(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(httpx.Response(200, json={"task_id": "t"}))
    out = client.request("POST", "unibox/compose", body={"to": ["a@example.com"]}, idempotency_key="k-1")
    assert api.last.url.path == "/v1/unibox/compose"
    assert api.last.headers["idempotency-key"] == "k-1"
    assert json.loads(api.last.content) == {"to": ["a@example.com"]}
    assert out == {"task_id": "t"}

    rows = list(client.paginate("/campaigns"))
    assert len(rows) == 3


def test_generic_request_returns_bytes_for_non_json(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(httpx.Response(200, content=b"plain text", headers={"Content-Type": "text/plain"}))
    assert client.request("GET", "/something") == b"plain text"


def test_empty_bodies_return_none(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(httpx.Response(204))
    api.queue.append(httpx.Response(200, content=b""))
    assert client.request("DELETE", "/contacts/x") is None
    assert client.request("DELETE", "/campaigns/x/steps/y") is None


def test_unknown_fields_are_kept(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(httpx.Response(200, json={"user_id": "u", "brand_new_field": {"a": 1}}))
    me = client.me.get()
    assert me["user_id"] == "u"
    assert dict(me)["brand_new_field"] == {"a": 1}


def test_query_and_body_encoding(api: MockAPI, client: AyInbox) -> None:
    when = dt.datetime(2026, 11, 13, 9, 30, tzinfo=dt.timezone.utc)
    api.queue.append(httpx.Response(200, json={"data": [], "pagination": {}}))
    client.unibox.list_threads(since=when, automated=False)
    params = dict(api.last.url.params)
    assert params == {"since": "2026-11-13T09:30:00Z", "automated": "false"}

    api.queue.append(httpx.Response(200, json={}))
    client.campaigns.update("c", start_date=when, end_date=None)
    assert json.loads(api.last.content) == {"start_date": "2026-11-13T09:30:00Z", "end_date": None}


def test_invalid_idempotency_key_is_refused_locally(client: AyInbox) -> None:
    with pytest.raises(ValueError):
        client.campaigns.create(name="x", idempotency_key="has space")
    with pytest.raises(ValueError):
        client.campaigns.create(name="x", idempotency_key="")


def test_per_request_timeout(api: MockAPI, client: AyInbox) -> None:
    client.me.get(timeout=3.0)
    assert api.last.extensions["timeout"]["read"] == 3.0
    client.me.get()
    assert api.last.extensions["timeout"]["read"] == 30.0


def test_context_manager_closes_owned_client() -> None:
    with AyInbox(TEST_KEY) as c:
        assert not c._http.is_closed
    assert c._http.is_closed
