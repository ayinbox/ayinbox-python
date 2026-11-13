from __future__ import annotations

import json
from typing import Any, Callable, Optional

import httpx
import pytest

from ayinbox import AyInbox, SyncPage

from .conftest import MockAPI

CID = "11111111-1111-4111-8111-111111111111"
SID = "44444444-4444-4444-8444-111111111111"
KID = "22222222-2222-4222-8222-111111111111"
MID = "33333333-3333-4333-8333-111111111111"
UID = "55555555-5555-4555-8555-111111111111"
DID = "bbbbbbbb-bbbb-4bbb-8bbb-111111111111"
TID = "66666666-6666-4666-8666-111111111111"
WID = "77777777-7777-4777-8777-111111111111"
XID = "88888888-8888-4888-8888-111111111111"

Call = Callable[[AyInbox], Any]

# (name, call, method, path, query, body). body None means no body sent.
# fmt: off
CASES = [
    ("me.get", lambda c: c.me.get(), "GET", "/v1/me", {}, None),
    ("campaigns.list", lambda c: c.campaigns.list(status="active", limit=10), "GET", "/v1/campaigns",
     {"status": "active", "limit": "10"}, None),
    ("campaigns.get", lambda c: c.campaigns.get(CID), "GET", f"/v1/campaigns/{CID}", {}, None),
    ("campaigns.create", lambda c: c.campaigns.create(name="Q4", daily_limit=30), "POST", "/v1/campaigns", {},
     {"name": "Q4", "daily_limit": 30}),
    ("campaigns.update", lambda c: c.campaigns.update(CID, name="New", start_date=None), "PATCH",
     f"/v1/campaigns/{CID}", {}, {"name": "New", "start_date": None}),
    ("campaigns.delete", lambda c: c.campaigns.delete(CID), "DELETE", f"/v1/campaigns/{CID}", {}, None),
    ("campaigns.start", lambda c: c.campaigns.start(CID, acknowledge_list_risk=True), "POST",
     f"/v1/campaigns/{CID}/start", {}, {"acknowledge_list_risk": True}),
    ("campaigns.pause", lambda c: c.campaigns.pause(CID), "POST", f"/v1/campaigns/{CID}/stop", {}, None),
    ("campaigns.duplicate", lambda c: c.campaigns.duplicate(CID, name="Copy"), "POST",
     f"/v1/campaigns/{CID}/duplicate", {}, {"name": "Copy"}),
    ("campaigns.overview", lambda c: c.campaigns.overview(), "GET", "/v1/campaigns-overview", {}, None),
    ("campaigns.steps.list", lambda c: c.campaigns.steps.list(CID), "GET", f"/v1/campaigns/{CID}/steps", {}, None),
    ("campaigns.steps.create", lambda c: c.campaigns.steps.create(CID, subject="Hi", wait_after=2), "POST",
     f"/v1/campaigns/{CID}/steps", {}, {"subject": "Hi", "wait_after": 2}),
    ("campaigns.steps.update", lambda c: c.campaigns.steps.update(CID, SID, subject="Hello"), "PATCH",
     f"/v1/campaigns/{CID}/steps/{SID}", {}, {"subject": "Hello"}),
    ("campaigns.steps.delete", lambda c: c.campaigns.steps.delete(CID, SID), "DELETE",
     f"/v1/campaigns/{CID}/steps/{SID}", {}, None),
    ("campaigns.leads.list", lambda c: c.campaigns.leads.list(CID, lead_status="replied", limit=5), "POST",
     "/v1/contacts/search", {"limit": "5"}, {"campaign_ids": [CID], "lead_status": "replied"}),
    ("campaigns.leads.add", lambda c: c.campaigns.leads.add(CID, {"email": "a@example.com"}), "POST",
     "/v1/contacts", {}, [{"email": "a@example.com", "campaigns": [CID]}]),
    ("campaigns.leads.get_hold", lambda c: c.campaigns.leads.get_hold(CID, KID), "GET",
     f"/v1/campaigns/{CID}/leads/{KID}/hold", {}, None),
    ("campaigns.leads.pause", lambda c: c.campaigns.leads.pause(CID, KID, until="2026-12-01T00:00:00Z"), "POST",
     f"/v1/campaigns/{CID}/leads/{KID}/pause", {}, {"until": "2026-12-01T00:00:00Z"}),
    ("campaigns.leads.resume", lambda c: c.campaigns.leads.resume(CID, KID), "POST",
     f"/v1/campaigns/{CID}/leads/{KID}/resume", {}, None),
    ("contacts.list", lambda c: c.contacts.list(query="lee", sort_by="email", category=TID), "POST",
     "/v1/contacts/search", {"category": TID}, {"query": "lee", "sort_by": "email"}),
    ("contacts.get", lambda c: c.contacts.get(KID), "GET", f"/v1/contacts/{KID}", {}, None),
    ("contacts.create", lambda c: c.contacts.create({"email": "lee@example.com"}), "POST", "/v1/contacts", {},
     {"email": "lee@example.com"}),
    ("contacts.update", lambda c: c.contacts.update(KID, company="Acme"), "PATCH", f"/v1/contacts/{KID}", {},
     {"company": "Acme"}),
    ("contacts.delete", lambda c: c.contacts.delete(KID), "DELETE", f"/v1/contacts/{KID}", {}, None),
    ("contacts.bulk_delete", lambda c: c.contacts.bulk_delete([KID]), "DELETE", "/v1/contacts", {}, [KID]),
    ("mailboxes.list", lambda c: c.mailboxes.list(q="sales"), "GET", "/v1/emails", {"q": "sales"}, None),
    ("mailboxes.get", lambda c: c.mailboxes.get(MID), "GET", f"/v1/emails/{MID}", {}, None),
    ("mailboxes.get_sync", lambda c: c.mailboxes.get_sync(MID), "GET", f"/v1/emails/{MID}/sync", {}, None),
    ("unibox.list_threads",
     lambda c: c.unibox.list_threads(folder="inbox", unseen=True, from_="lee@example.com", email_ids=[MID, MID]),
     "GET", "/v1/unibox",
     {"folder": "inbox", "unseen": "true", "from": "lee@example.com", "email_ids": f"{MID},{MID}"}, None),
    ("unibox.get_thread", lambda c: c.unibox.get_thread("thread-example-001", email_id=MID), "GET",
     "/v1/unibox/thread", {"thread_id": "thread-example-001", "email_id": MID}, None),
    ("unibox.get_message", lambda c: c.unibox.get_message(UID), "GET", f"/v1/unibox/{UID}", {}, None),
    ("unibox.unread_count", lambda c: c.unibox.unread_count(email_id=MID), "GET", "/v1/unibox/count",
     {"email_id": MID}, None),
    ("unibox.reply",
     lambda c: c.unibox.reply(email_account_id=MID, to=["lee@example.com"], subject="Re: Hi", body_plain="Thanks"),
     "POST", "/v1/unibox/reply", {},
     {"email_account_id": MID, "to": ["lee@example.com"], "subject": "Re: Hi", "body_plain": "Thanks"}),
    ("unibox.list_drafts", lambda c: c.unibox.list_drafts(), "GET", "/v1/unibox/drafts", {}, None),
    ("unibox.save_draft", lambda c: c.unibox.save_draft(DID, subject="Draft"), "PUT", f"/v1/unibox/drafts/{DID}",
     {}, {"subject": "Draft"}),
    ("unibox.delete_draft", lambda c: c.unibox.delete_draft(DID), "DELETE", f"/v1/unibox/drafts/{DID}", {}, None),
    ("unibox.list_agent_drafts", lambda c: c.unibox.list_agent_drafts(), "GET", "/v1/unibox/agent-drafts", {},
     None),
    ("unibox.approve_agent_draft", lambda c: c.unibox.approve_agent_draft(DID, acknowledge_flags=True), "POST",
     f"/v1/unibox/agent-drafts/{DID}/approve", {}, {"acknowledge_flags": True}),
    ("unibox.discard_agent_draft", lambda c: c.unibox.discard_agent_draft(DID), "POST",
     f"/v1/unibox/agent-drafts/{DID}/discard", {}, None),
    ("templates.list", lambda c: c.templates.list(q="intro"), "GET", "/v1/templates", {"q": "intro"}, None),
    ("templates.get", lambda c: c.templates.get(TID), "GET", f"/v1/templates/{TID}", {}, None),
    ("templates.create", lambda c: c.templates.create(name="Intro", subject="Hi"), "POST", "/v1/templates", {},
     {"name": "Intro", "subject": "Hi"}),
    ("templates.update", lambda c: c.templates.update(TID, subject="Hello"), "PATCH", f"/v1/templates/{TID}", {},
     {"subject": "Hello"}),
    ("templates.delete", lambda c: c.templates.delete(TID), "DELETE", f"/v1/templates/{TID}", {}, None),
    ("webhooks.list", lambda c: c.webhooks.list(), "GET", "/v1/webhooks", {}, None),
    ("webhooks.create",
     lambda c: c.webhooks.create(url="https://hooks.example.com/ayinbox", event_types=["campaign.reply_received"]),
     "POST", "/v1/webhooks", {},
     {"url": "https://hooks.example.com/ayinbox", "event_types": ["campaign.reply_received"]}),
    ("webhooks.update", lambda c: c.webhooks.update(WID, url="https://hooks.example.com/x", enabled=False),
     "PATCH", f"/v1/webhooks/{WID}", {}, {"url": "https://hooks.example.com/x", "enabled": False}),
    ("webhooks.delete", lambda c: c.webhooks.delete(WID), "DELETE", f"/v1/webhooks/{WID}", {}, None),
    ("webhooks.rotate_secret", lambda c: c.webhooks.rotate_secret(WID), "POST",
     f"/v1/webhooks/{WID}/rotate-secret", {}, None),
    ("webhooks.verify", lambda c: c.webhooks.verify(WID), "POST", f"/v1/webhooks/{WID}/verify", {}, None),
    ("webhooks.event_types", lambda c: c.webhooks.event_types(), "GET", "/v1/webhooks/event-types", {}, None),
    ("webhooks.list_deliveries", lambda c: c.webhooks.list_deliveries(status="failed", limit=20), "GET",
     "/v1/webhooks/deliveries", {"status": "failed", "limit": "20"}, None),
    ("analytics.dashboard", lambda c: c.analytics.dashboard(period="30d", campaign_ids=[CID]), "GET",
     "/v1/analytics/dashboard", {"period": "30d", "campaign_ids": CID}, None),
    ("analytics.campaign", lambda c: c.analytics.campaign(CID, from_="2026-11-01", to="2026-11-12"), "GET",
     f"/v1/analytics/campaigns/{CID}", {"from": "2026-11-01", "to": "2026-11-12"}, None),
    ("analytics.campaign_daily", lambda c: c.analytics.campaign_daily(CID), "GET",
     f"/v1/analytics/campaigns/{CID}/daily", {}, None),
    ("analytics.accounts", lambda c: c.analytics.accounts(email_ids=[MID]), "GET", "/v1/analytics/accounts",
     {"email_ids": MID}, None),
    ("analytics.account", lambda c: c.analytics.account(MID), "GET", f"/v1/analytics/accounts/{MID}", {}, None),
    ("suppressions.list", lambda c: c.suppressions.list(q="example.org"), "GET", "/v1/suppressions",
     {"q": "example.org"}, None),
    ("suppressions.add", lambda c: c.suppressions.add(["no-reply@example.org"], reason="Asked"), "POST",
     "/v1/suppressions", {}, {"entries": [{"value": "no-reply@example.org"}], "reason": "Asked"}),
    ("suppressions.remove", lambda c: c.suppressions.remove(XID), "DELETE", f"/v1/suppressions/{XID}", {}, None),
    ("ai_tools.list", lambda c: c.ai_tools.list(format="openai", toolsets=["inbox", "campaigns"]), "GET",
     "/v1/ai/tools", {"format": "openai", "toolsets": "inbox,campaigns"}, None),
    ("ai_tools.call", lambda c: c.ai_tools.call("list_campaigns", {"limit": 5}), "POST",
     "/v1/ai/tools/list_campaigns/call", {}, {"limit": 5}),
]
# fmt: on

# These routes have no fixture in index.json, so the test queues a generic answer.
NO_FIXTURE = {"analytics.campaign_daily", "analytics.accounts", "analytics.account"}


def test_case_count() -> None:
    assert len(CASES) == 62
    assert len({c[0] for c in CASES}) == 62


@pytest.mark.parametrize("name,call,method,path,query,body", CASES, ids=[c[0] for c in CASES])
def test_method_sends_the_documented_request(
    api: MockAPI,
    client: AyInbox,
    name: str,
    call: Call,
    method: str,
    path: str,
    query: dict,  # type: ignore[type-arg]
    body: Optional[Any],
) -> None:
    if name in NO_FIXTURE:
        api.queue.append(lambda r: httpx.Response(200, json={"data": [], "pagination": {}}))
    result = call(client)
    req = api.last
    assert req.method == method
    assert req.url.path == path
    assert dict(req.url.params) == query
    if body is None:
        assert req.content == b""
        assert "content-type" not in req.headers
    else:
        assert json.loads(req.content) == body
        assert req.headers["content-type"] == "application/json"
    if isinstance(result, SyncPage):
        assert isinstance(result.data, list)
    elif result is not None:
        assert isinstance(result, (dict, list))


def test_happy_path_values(client: AyInbox) -> None:
    me = client.me.get()
    assert me["email"] == "dana@example.com" and "read_campaigns" in me["scopes"]

    campaign = client.campaigns.get(CID)
    assert campaign["id"] and campaign["status"]

    created = client.contacts.create([{"email": "lee@example.com"}])
    assert isinstance(created, list) and created[0]["email"] == "lee@example.com"

    msg = client.unibox.get_message(UID)
    assert msg["from"] == ["Lee Example <lee@example.com>"] and msg["ReplyTo"] == []

    hook = client.webhooks.create(url="https://hooks.example.com/ayinbox")
    assert hook["secret"].startswith("whsec_")

    client.campaigns.delete(CID)
    client.campaigns.steps.delete(CID, SID)
    assert client.unibox.delete_draft(DID) == {"deleted": True}

    started = client.campaigns.start(CID)
    assert started["status"] == "started"

    tool = client.ai_tools.call("list_campaigns")
    assert tool["data"]["untrusted"] is False

    leads = client.campaigns.leads.list(CID)
    assert leads.data[0]["campaign_lead"]["status"]


def test_leads_add_keeps_existing_campaigns(api: MockAPI, client: AyInbox) -> None:
    client.campaigns.leads.add(CID, [{"email": "a@example.com", "campaigns": ["other"]}, {"email": "b@example.com"}])
    assert api.last_json() == [
        {"email": "a@example.com", "campaigns": ["other", CID]},
        {"email": "b@example.com", "campaigns": [CID]},
    ]


def test_list_deliveries_for_one_endpoint(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(lambda r: httpx.Response(200, json={"data": [], "pagination": {}}))
    client.webhooks.list_deliveries(webhook_id=WID)
    assert api.last.url.path == f"/v1/webhooks/{WID}/deliveries"


def test_path_params_are_escaped(api: MockAPI, client: AyInbox) -> None:
    api.queue.append(lambda r: httpx.Response(200, json={}))
    client.campaigns.get("a/b")
    assert api.last.url.raw_path.startswith(b"/v1/campaigns/a%2Fb")
