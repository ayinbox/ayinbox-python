# ayinbox

The official Python client for the [AY Inbox](https://ayinbox.com) REST API.

AY Inbox is a hosted cold email platform: it sends cold email at a paced daily volume, brings every reply into one inbox (Unibox), drafts answers from a per-campaign brain, and can offer a meeting time from Cal.com or Calendly. Everything is on a REST API at `https://api.ayinbox.com/v1`. This library wraps it with a sync client, an async client, typed errors, retries, pagination and webhook signature checks.

AY Inbox is a hosted service. This repository holds the Python client for its public API. The service itself is not open source.

Access to the hosted service is invite only for now: ask at team@ayinbox.com.

## Install

Not on PyPI yet. Install from GitHub:

```sh
pip install "ayinbox @ git+https://github.com/ayinbox/ayinbox-python@main"
```

Python 3.9 or later. The only runtime dependency is [httpx](https://www.python-httpx.org/).

## Quick start

Create an API key in the dashboard (`https://app.ayinbox.com`) and export it as `AYINBOX_API_KEY`.

```python
from ayinbox import AyInbox, ConflictError, PermissionDeniedError

client = AyInbox()  # reads AYINBOX_API_KEY

me = client.me.get()
print(me["email"], me["scopes"])

for campaign in client.campaigns.list(limit=50):  # walks every page
    print(campaign["id"], campaign["status"], campaign["name"])

try:
    contacts = client.contacts.create(
        {"email": "lee@example.com", "first_name": "Lee"},
        idempotency_key="import-lee-2026-11-13",
    )
    print(contacts[0]["id"])
except PermissionDeniedError as err:
    print("missing scope:", err.code, err.request_id)
except ConflictError as err:
    print("conflict:", err.code)
```

The async client has the same surface, with every call awaited:

```python
import asyncio
from ayinbox import AsyncAyInbox

async def main() -> None:
    async with AsyncAyInbox() as client:
        page = await client.campaigns.list()
        async for campaign in page:
            print(campaign["name"])

asyncio.run(main())
```

## Client options

```python
AyInbox(
    api_key=None,            # falls back to AYINBOX_API_KEY
    base_url=None,           # falls back to AYINBOX_BASE_URL, then https://api.ayinbox.com/v1
    timeout=30.0,            # seconds, or an httpx.Timeout
    max_retries=2,           # 0 disables retries
    default_headers=None,    # sent on every request
    http_client=None,        # your own httpx.Client (httpx.AsyncClient for AsyncAyInbox)
)
```

API keys start with `aybox_` and OAuth access tokens with `ayat_`; both work. The client sends `Authorization: Bearer <credential>`, `User-Agent: ayinbox-python/<version>` and `Accept: application/json`. The key never appears in `repr()` or in an error message.

Every method also takes `timeout=` and `extra_headers=` for that one call (for example `extra_headers={"X-Request-Id": "my-trace-id"}`), and every method that changes something takes `idempotency_key=`.

## Resources

| Attribute | Methods |
|---|---|
| `client.me` | `get` |
| `client.campaigns` | `list`, `get`, `create`, `update`, `delete`, `start`, `pause`, `duplicate`, `overview` |
| `client.campaigns.steps` | `list`, `create`, `update`, `delete` |
| `client.campaigns.leads` | `list`, `add`, `get_hold`, `pause`, `resume` |
| `client.contacts` | `list`, `get`, `create`, `update`, `delete`, `bulk_delete` |
| `client.mailboxes` | `list`, `get`, `get_sync` |
| `client.unibox` | `list_threads`, `get_thread`, `get_message`, `unread_count`, `reply`, `list_drafts`, `save_draft`, `delete_draft`, `list_agent_drafts`, `approve_agent_draft`, `discard_agent_draft` |
| `client.templates` | `list`, `get`, `create`, `update`, `delete` |
| `client.webhooks` | `list`, `create`, `update`, `delete`, `rotate_secret`, `verify`, `event_types`, `list_deliveries`, plus `verify_signature` and `construct_event` |
| `client.analytics` | `dashboard`, `campaign`, `campaign_daily`, `accounts`, `account` |
| `client.suppressions` | `list`, `add`, `remove` |
| `client.ai_tools` | `list`, `call` |

Notes on shapes:

- Responses are plain dicts. `ayinbox.types` holds `TypedDict`s for the documented fields (`Campaign`, `Contact`, `Message`, ...), so editors and type checkers know them. Fields the API adds later stay in the dict.
- Request fields beyond the required ones go in as keyword arguments and are sent as the JSON body: `client.campaigns.create(name="Q4", daily_limit=30, timezone="Europe/London")`. A keyword set to `None` is sent as JSON `null`, which is how `client.campaigns.update(campaign_id, start_date=None)` clears a date.
- `from` is a Python keyword, so the `from` query parameter is `from_=` (`unibox.list_threads`, `analytics.campaign`).
- `webhooks.update` replaces the whole endpoint: send the full desired state. An omitted `enabled` becomes true.
- `contacts.create` upserts by email and always returns a list.
- `webhooks.verify` re-sends the endpoint's verification challenge. Checking a delivery's signature is `verify_signature`.

Any route without a method here is reachable through `request`:

```python
client.request("GET", f"/campaigns/{campaign_id}/send-plan")
client.request("POST", "/unibox/compose", body={...}, idempotency_key="compose-1")
```

`request` goes through the same authentication, retries and error mapping, and returns the decoded JSON (`None` for an empty body, raw `bytes` for a non-JSON body).

## Errors

Every non-2xx answer raises a subclass of `ayinbox.APIError`, which carries `status`, `code` (the stable machine key to branch on), `message`, `reason`, `request_id`, `retry_after`, `body` and `headers`.

| Status | Error |
|---|---|
| 400 | `BadRequestError` (subclass of `ValidationError`) |
| 401 | `AuthenticationError`, for example `api_key_holder_left` when the key's member left the workspace |
| 402 | `PaymentRequiredError` (`insufficient_credits`) |
| 403 | `PermissionDeniedError` (a missing scope, `api_key_mailbox_limited`, ...) |
| 404 | `NotFoundError` |
| 409 | `ConflictError` (`idempotency_outcome_unknown`, `idempotent_secret_withheld`, `draft_flagged`, ...) |
| 422 | `UnprocessableEntityError` (subclass of `ValidationError`) |
| 429 | `RateLimitError`, with `retry_after` in seconds |
| 503 | `ServiceUnavailableError` (subclass of `ServerError`) |
| other 5xx | `InternalServerError` (subclass of `ServerError`) |

A request that gets no HTTP answer raises `APIConnectionError`, and a timeout raises `APITimeoutError` (a subclass of it). Everything this library raises inherits from `AyInboxError`.

Validation messages name the fields at fault (`"to" is required`). There is no per-field structure, so show `message` as it is.

## Retries and timeouts

The client retries a request up to `max_retries` times (default 2) when:

- the answer is `429`, `502`, `503` or `504`, or
- the connection failed or timed out.

It waits for `Retry-After` when the API sends one (capped at 120 seconds), and otherwise backs off exponentially with full jitter (0.5 seconds base, 8 seconds cap). A `500` is not retried, because its outcome is unknown.

A `POST` or `PATCH` without an idempotency key is never retried, except on `429` (a rate-limited request never ran). The client does not generate keys for you: pass `idempotency_key=` on any create or update you want retried. `GET`, `PUT` and `DELETE` are retried, and so is the contact search (`POST /contacts/search`), which only reads.

The default timeout is 30 seconds. Pass `timeout=` to the client or to one call.

## Pagination

List methods that page return a `SyncPage` (or `AsyncPage`) holding one page: `page.data`, `page.next_cursor`, `page.has_more`, `page.total` (when the endpoint gives one) and `page.raw` (the whole response, where the `counts` and `lead_counts` of a contact search live).

Iterating a page walks every page after it:

```python
for contact in client.contacts.list(query="example.com", sort_by="email"):
    print(contact["email"])

page = client.mailboxes.list(limit=100)
while True:
    handle(page.data)
    if not page.has_next_page():
        break
    page = page.get_next_page()
```

Paged methods: `campaigns.list`, `campaigns.leads.list`, `contacts.list`, `mailboxes.list`, `unibox.list_threads`, `unibox.get_thread`, `webhooks.list_deliveries`, `analytics.accounts` and `suppressions.list`. `client.paginate(path, query=...)` walks any other `data` + `pagination` route. A contact search resends the same body on every page, since its cursor is bound to the sort order. A `429` in the middle of a walk is waited out like any other retry.

Recommended `limit` values are 1 to 100.

## Idempotency

Every method that changes something accepts `idempotency_key=`, sent as the `Idempotency-Key` header (1 to 255 visible ASCII characters). For 24 hours the API replays the stored answer to a repeat of the same request with the same key. The same key on a different request answers `409 conflict`. When the first attempt ended in a server error or never finished, the key answers `409 idempotency_outcome_unknown`: check whether the change happened before trying again with a new key. Answers that hold a secret shown once (creating a webhook endpoint, rotating its secret) are not stored, so a repeat answers `409 idempotent_secret_withheld`.

## Webhooks

Every delivery carries `X-Ayinbox-Signature: t=<unix-seconds>,v1=<hex>`. Verify it against the raw request body, before parsing it:

```python
from ayinbox import SignatureVerificationError, construct_event, verify_signature

ok = verify_signature(raw_body, request.headers["X-Ayinbox-Signature"], secret)

try:
    event = construct_event(raw_body, request.headers["X-Ayinbox-Signature"], secret)
except SignatureVerificationError:
    ...  # answer 400
print(event["event_type"], event["data"])
```

`secret` is the endpoint secret including its `whsec_` prefix. The check uses HMAC-SHA256 with a constant-time compare and refuses timestamps more than 300 seconds away from now (`tolerance=` changes that). Deduplicate on the `X-Ayinbox-Event-Id` header, which stays the same across retries. `examples/verify_webhook.py` is a runnable receiver.

## Calls that send email

These calls put real email on the wire:

- `campaigns.start` (`POST /campaigns/{id}/start`) needs `START_CAMPAIGNS` or `SEND_CAMPAIGNS`.
- `campaigns.update` with `status="active"` (and `completed` or `paused_undeliverable`) needs `START_CAMPAIGNS` or `SEND_CAMPAIGNS` in addition to `WRITE_CAMPAIGNS`.
- `campaigns.leads.resume` on a finished campaign needs `START_CAMPAIGNS` or `SEND_CAMPAIGNS`.
- `unibox.reply` and `unibox.approve_agent_draft` need `WRITE_UNIBOX`. A key with `WRITE_UNIBOX` can send replies from any mailbox it can reach.
- Through `request`: `POST /unibox/compose`, `POST /emails/{id}/send`, `POST /campaigns/{id}/test-email`, the first-email review queue (`/campaigns/{id}/reviews/...`) and placement tests need `SEND_CAMPAIGNS` (compose needs `WRITE_UNIBOX`).

Adding contacts can send mail without calling start: contacts added to an `active` campaign are queued, a `completed` campaign starts again on its own when leads are added, and a contact that comes to match a segment linked to a sending campaign is enrolled. That covers `contacts.create`, `contacts.update` with `campaigns` and `campaigns.leads.add`.

`START_CAMPAIGNS` starts, resumes and pauses campaigns and nothing else. `SEND_CAMPAIGNS` covers everything `START_CAMPAIGNS` covers plus the other sending actions. `WRITE_CAMPAIGNS` alone edits drafts and pauses, and cannot start anything.

A key for a model that reads the inbox should use the "Agent: read and draft" preset (84574239): every read scope plus `AI_DRAFT`, with nothing that writes or sends.

Some calls spend workspace credits (AI drafts, research, enrichment, paid tools). They answer `402 insufficient_credits` when the balance is out.

Retrying a send without an idempotency key can send twice. Pass an idempotency key on every mutating call you might retry.

## Development

```sh
uv venv && uv pip install -e . pytest mypy==2.4.1 ruff==0.17.5
.venv/bin/pytest
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/mypy
```

`src/ayinbox/_async_resources.py` is generated from `_resources.py`: run `python scripts/gen_async.py` after editing the sync resources. The tests run against a local mock transport fed from `tests/fixtures/`, with no network access.

## Links

- API reference: https://docs.ayinbox.com/api/
- Docs: https://docs.ayinbox.com
- Security reports: [SECURITY.md](SECURITY.md)
- Contact: team@ayinbox.com

## License

MIT. See [LICENSE](LICENSE).
