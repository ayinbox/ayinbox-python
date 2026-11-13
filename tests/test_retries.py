from __future__ import annotations

from typing import List

import httpx
import pytest

import ayinbox
from ayinbox import AyInbox

from .conftest import TEST_KEY, MockAPI, error_response


def test_retry_then_success_on_503(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    api.queue.append(error_response("503_service_unavailable.json"))
    me = client.me.get()
    assert me["email"] == "dana@example.com"
    assert len(api.requests) == 2
    assert sleeps == [5.0]  # Retry-After from the fixture


def test_retry_then_success_on_429_with_retry_after(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    api.queue.append(error_response("429_api_key_rate_limited.json"))
    client.campaigns.get("11111111-1111-4111-8111-111111111111")
    assert len(api.requests) == 2
    assert sleeps == [12.0]


def test_keyless_post_is_retried_on_429(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    api.queue.append(error_response("429_category_rate_limited.json"))
    client.templates.create(name="Intro")
    assert len(api.requests) == 2
    assert sleeps == [12.0]


def test_keyless_post_is_not_retried_on_503(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    api.queue.append(error_response("503_service_unavailable.json"))
    with pytest.raises(ayinbox.ServiceUnavailableError):
        client.campaigns.create(name="Q4")
    assert len(api.requests) == 1
    assert sleeps == []


def test_keyless_patch_is_not_retried_on_connection_error(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(httpx.ConnectError("refused"))
    with pytest.raises(ayinbox.APIConnectionError):
        client.contacts.update("22222222-2222-4222-8222-111111111111", company="Acme")
    assert len(api.requests) == 1


def test_post_with_key_is_retried_and_reuses_the_key(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    api.queue.append(error_response("503_service_unavailable.json"))
    api.queue.append(httpx.Response(502))
    client.contacts.create({"email": "lee@example.com"}, idempotency_key="import-2026-11-13")
    assert len(api.requests) == 3
    assert [r.headers["idempotency-key"] for r in api.requests] == ["import-2026-11-13"] * 3
    assert sleeps[0] == 5.0
    assert 0 <= sleeps[1] <= 1.0  # backoff with jitter, attempt 1: up to 0.5 * 2


def test_idempotency_key_header_sent(api: MockAPI, client: AyInbox) -> None:
    client.campaigns.start("11111111-1111-4111-8111-111111111111", idempotency_key="start-q4")
    assert api.last.headers["idempotency-key"] == "start-q4"


def test_contact_search_is_a_safe_post(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    api.queue.append(httpx.Response(504))
    page = client.contacts.list()
    assert len(api.requests) == 2
    assert page.data


def test_500_is_not_retried(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(error_response("500_internal_error.json"))
    with pytest.raises(ayinbox.InternalServerError):
        client.me.get()
    assert len(api.requests) == 1


def test_idempotency_outcome_unknown_is_not_retried(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(error_response("409_idempotency_outcome_unknown.json"))
    with pytest.raises(ayinbox.ConflictError) as info:
        client.campaigns.create(name="Q4", idempotency_key="k")
    assert info.value.code == "idempotency_outcome_unknown"
    assert len(api.requests) == 1


def test_get_connection_error_is_retried_then_raised(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    for _ in range(3):
        api.queue.append(httpx.ConnectError("refused"))
    with pytest.raises(ayinbox.APIConnectionError):
        client.me.get()
    assert len(api.requests) == 3
    assert len(sleeps) == 2


def test_timeout_is_its_own_error(api: MockAPI, sleeps: List[float]) -> None:
    api.queue.append(httpx.ReadTimeout("slow"))
    c = AyInbox(TEST_KEY, max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(api.handler)))
    with pytest.raises(ayinbox.APITimeoutError):
        c.me.get()


def test_max_retries_zero_disables(api: MockAPI, sleeps: List[float]) -> None:
    api.queue.append(error_response("503_service_unavailable.json"))
    c = AyInbox(TEST_KEY, max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(api.handler)))
    c._sleep = sleeps.append
    with pytest.raises(ayinbox.ServiceUnavailableError):
        c.me.get()
    assert sleeps == []


def test_retry_after_is_capped(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    api.queue.append(httpx.Response(429, headers={"Retry-After": "3600"}, json={"code": "rate_limit_exceeded"}))
    client.me.get()
    assert sleeps == [120.0]


def test_backoff_without_retry_after(api: MockAPI, client: AyInbox, sleeps: List[float]) -> None:
    client._random = lambda: 1.0
    api.queue.extend([httpx.Response(503), httpx.Response(503)])
    client.me.get()
    assert sleeps == [0.5, 1.0]
