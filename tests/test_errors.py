from __future__ import annotations

import json
from typing import Type

import httpx
import pytest

import ayinbox
from ayinbox import AyInbox

from .conftest import FIXTURES, MockAPI, error_response

ERROR_CASES = [
    ("400_bad_request.json", ayinbox.BadRequestError, "bad_request"),
    ("400_invalid_cursor.json", ayinbox.BadRequestError, "bad_request"),
    ("401_unauthorized.json", ayinbox.AuthenticationError, "unauthorized"),
    ("401_api_key_holder_left.json", ayinbox.AuthenticationError, "api_key_holder_left"),
    ("402_insufficient_credits.json", ayinbox.PaymentRequiredError, "insufficient_credits"),
    ("403_forbidden.json", ayinbox.PermissionDeniedError, "forbidden"),
    ("403_api_key_mailbox_limited.json", ayinbox.PermissionDeniedError, "api_key_mailbox_limited"),
    ("404_not_found.json", ayinbox.NotFoundError, "not_found"),
    ("409_conflict.json", ayinbox.ConflictError, "conflict"),
    ("409_idempotency_outcome_unknown.json", ayinbox.ConflictError, "idempotency_outcome_unknown"),
    ("409_idempotent_secret_withheld.json", ayinbox.ConflictError, "idempotent_secret_withheld"),
    ("422_unprocessable.json", ayinbox.UnprocessableEntityError, "unprocessable"),
    ("429_api_key_rate_limited.json", ayinbox.RateLimitError, "rate_limit_exceeded"),
    ("429_category_rate_limited.json", ayinbox.RateLimitError, "rate_limit_exceeded"),
    ("500_internal_error.json", ayinbox.InternalServerError, "internal_error"),
    ("503_service_unavailable.json", ayinbox.ServiceUnavailableError, "service_unavailable"),
]


@pytest.mark.parametrize("name,cls,code", ERROR_CASES, ids=[c[0] for c in ERROR_CASES])
def test_error_fixture_maps_to_typed_error(name: str, cls: Type[ayinbox.APIError], code: str) -> None:
    api = MockAPI()
    responses = [error_response(name) for _ in range(5)]
    api.queue.extend(responses)
    c = AyInbox("aybox_x", max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(api.handler)))
    with pytest.raises(cls) as info:
        c.me.get()
    err = info.value
    body = json.loads((FIXTURES / "errors" / name).read_text())
    assert isinstance(err, ayinbox.APIError)
    assert err.status == responses[0].status_code
    assert err.code == code
    assert err.message == body["message"]
    assert err.reason == body.get("reason")
    assert err.body == body
    assert code in str(err)


def test_validation_parent_and_server_parent() -> None:
    assert issubclass(ayinbox.BadRequestError, ayinbox.ValidationError)
    assert issubclass(ayinbox.UnprocessableEntityError, ayinbox.ValidationError)
    assert issubclass(ayinbox.ServiceUnavailableError, ayinbox.ServerError)
    assert issubclass(ayinbox.InternalServerError, ayinbox.ServerError)
    assert issubclass(ayinbox.APITimeoutError, ayinbox.APIConnectionError)


def test_category_429_without_code_or_request_id(api: MockAPI) -> None:
    api.queue.append(error_response("429_category_rate_limited.json", {"Retry-After": ""}))
    c = AyInbox("aybox_x", max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(api.handler)))
    with pytest.raises(ayinbox.RateLimitError) as info:
        c.templates.list()
    err = info.value
    assert err.code == "rate_limit_exceeded"  # taken from "error", which is a code here
    assert err.request_id is None
    assert err.retry_after == 12.0  # ceil(retry_after_ms / 1000)
    assert err.message == "Rate limit exceeded for write operations"


def test_api_key_429_retry_after_and_request_id(api: MockAPI) -> None:
    api.queue.append(error_response("429_api_key_rate_limited.json"))
    c = AyInbox("aybox_x", max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(api.handler)))
    with pytest.raises(ayinbox.RateLimitError) as info:
        c.me.get()
    assert info.value.retry_after == 12.0
    assert info.value.request_id == "req-fixture-0001"
    assert info.value.headers["x-ratelimit-remaining"] == "0"


def test_request_id_falls_back_to_header(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(
        httpx.Response(404, json={"error": "Not Found", "message": "gone"}, headers={"X-Request-Id": "r9"})
    )
    with pytest.raises(ayinbox.NotFoundError) as info:
        client.me.get()
    assert info.value.request_id == "r9"
    assert info.value.code == "not_found"


def test_non_json_error_body(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(httpx.Response(502, content=b"<html>bad gateway</html>"))
    api.queue.append(httpx.Response(502, content=b"<html>bad gateway</html>"))
    api.queue.append(httpx.Response(502, content=b"<html>bad gateway</html>"))
    with pytest.raises(ayinbox.InternalServerError) as info:
        client.me.get()
    assert info.value.status == 502
    assert info.value.code == "internal_error"
    assert info.value.body == "<html>bad gateway</html>"


def test_unknown_4xx_is_base_api_error(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(httpx.Response(405, json={"error": "Method Not Allowed", "message": "no"}))
    with pytest.raises(ayinbox.APIError) as info:
        client.me.get()
    assert type(info.value) is ayinbox.APIError
    assert info.value.status == 405
