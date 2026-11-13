from __future__ import annotations

import json

import pytest

import ayinbox
from ayinbox import AyInbox, webhooks

from .conftest import FIXTURES

VECTOR = json.loads((FIXTURES / "webhook_signature.json").read_text())
SECRET: str = VECTOR["secret"]
BODY: str = VECTOR["body"]
HEADER: str = VECTOR["header"]
TS: int = VECTOR["timestamp"]


def test_vector_signature_matches() -> None:
    assert webhooks.compute_signature(BODY, SECRET, TS) == VECTOR["expected_v1"]


def test_valid_signature() -> None:
    assert ayinbox.verify_signature(BODY, HEADER, SECRET, now=TS)
    assert ayinbox.verify_signature(BODY.encode(), HEADER, SECRET, now=TS + 300)


def test_tampered_body_fails() -> None:
    assert not ayinbox.verify_signature(BODY.replace("reply_received", "email_opened"), HEADER, SECRET, now=TS)
    assert not ayinbox.verify_signature(BODY + "\n", HEADER, SECRET, now=TS)


def test_wrong_secret_fails() -> None:
    assert not ayinbox.verify_signature(BODY, HEADER, "whsec_other", now=TS)
    assert not ayinbox.verify_signature(BODY, HEADER, SECRET[len("whsec_") :], now=TS)


def test_outside_tolerance_fails() -> None:
    assert not ayinbox.verify_signature(BODY, HEADER, SECRET, now=TS + VECTOR["tolerance_seconds"] + 1)
    assert not ayinbox.verify_signature(BODY, HEADER, SECRET, now=TS - 301)
    assert ayinbox.verify_signature(BODY, HEADER, SECRET, now=TS + 1000, tolerance=1000)


def test_any_v1_may_match_and_other_schemes_are_ignored() -> None:
    header = f"t={TS},v0=abc,v1={'0' * 64},v1={VECTOR['expected_v1']}"
    assert ayinbox.verify_signature(BODY, header, SECRET, now=TS)


@pytest.mark.parametrize(
    "header",
    ["", "garbage", f"v1={VECTOR['expected_v1']}", f"t={TS}", f"t=abc,v1={VECTOR['expected_v1']}", f"t={TS},v1="],
)
def test_malformed_headers_fail(header: str) -> None:
    assert not ayinbox.verify_signature(BODY, header, SECRET, now=TS)


def test_construct_event() -> None:
    event = ayinbox.construct_event(BODY, HEADER, SECRET, now=TS)
    assert event["event_type"] == "campaign.reply_received"
    assert event["id"] == "00000000-0000-4000-8000-000000000001"
    with pytest.raises(ayinbox.SignatureVerificationError):
        ayinbox.construct_event(BODY, HEADER, "whsec_wrong", now=TS)


def test_available_on_the_resource(client: AyInbox) -> None:
    assert client.webhooks.verify_signature(BODY, HEADER, SECRET, now=TS)
