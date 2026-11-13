# Changelog

## 0.1.0 (unreleased)

First release.

- `AyInbox` (sync) and `AsyncAyInbox` (async) clients on httpx, sharing one request core.
- The 62 API methods across `me`, `campaigns` (with `steps` and `leads`), `contacts`, `mailboxes`, `unibox`, `templates`, `webhooks`, `analytics`, `suppressions` and `ai_tools`.
- Generic `request` and `paginate` for any other route.
- Typed errors mapped by status, with `code`, `message`, `reason`, `request_id` and `retry_after`.
- Retries on 429, 502, 503, 504 and connection errors, honouring `Retry-After`; no retry of a POST or PATCH without an idempotency key except on 429.
- Per-call idempotency key, timeout and extra headers.
- `SyncPage` and `AsyncPage` with auto-paging iteration.
- Webhook signature verification (`verify_signature`, `construct_event`) with a constant-time compare.
- `TypedDict` response types and `py.typed`.
