"""Async resources. Generated from _resources.py by scripts/gen_async.py: do not edit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence, Union, cast

from . import webhooks as _webhooks
from ._core import NOT_GIVEN, TimeoutTypes, path_param
from ._pagination import AsyncPage
from .types import (
    AgentDraftList,
    AiToolCallResult,
    Campaign,
    CampaignAnalytics,
    CampaignsOverview,
    CampaignStartResult,
    CampaignStopResult,
    Contact,
    ContactDetail,
    DashboardAnalytics,
    DataList,
    DeletedDraft,
    Delivery,
    DiscardResult,
    DraftList,
    EventTypeList,
    Identity,
    LeadHoldResult,
    Mailbox,
    MailboxSync,
    Message,
    MessagePreview,
    SavedDraft,
    SendResult,
    Step,
    Suppression,
    SuppressionAddResult,
    Template,
    TemplateList,
    UnreadCount,
    WebhookEndpoint,
    WebhookEndpointWithSecret,
    WebhookList,
    WebhookSecret,
    WebhookVerifyResult,
)

if TYPE_CHECKING:
    from ._client import AsyncAyInbox

Headers = Optional[Mapping[str, str]]
ContactsArg = Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]


def _body(params: Mapping[str, Any], **fixed: Any) -> Dict[str, Any]:
    out = dict(fixed)
    out.update(params)
    return out


def _optional(**values: Any) -> Dict[str, Any]:
    return {k: v for k, v in values.items() if v is not None}


class _Resource:
    def __init__(self, client: "AsyncAyInbox") -> None:
        self._client = client


class AsyncMe(_Resource):
    async def get(self, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> Identity:
        """``GET /me``: the identity behind the credential. Needs no scope."""
        return cast(Identity, await self._client._request("GET", "/me", timeout=timeout, extra_headers=extra_headers))


class AsyncCampaignSteps(_Resource):
    async def list(
        self, campaign_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None
    ) -> List[Step]:
        """``GET /campaigns/{id}/steps``: every step, in canvas order (not paginated)."""
        return cast(
            List[Step],
            await self._client._request(
                "GET", f"/campaigns/{path_param(campaign_id)}/steps", timeout=timeout, extra_headers=extra_headers
            ),
        )

    async def create(
        self,
        campaign_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> Step:
        """``POST /campaigns/{id}/steps``. Fields: name, subject, body_plain, body_html, wait_after, ...

        A step created here is not connected to the previous one. For a linear
        sequence, pass ``steps`` to ``campaigns.create``.
        """
        return cast(
            Step,
            await self._client._request(
                "POST",
                f"/campaigns/{path_param(campaign_id)}/steps",
                body=dict(params),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def update(
        self,
        campaign_id: str,
        step_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> Step:
        """``PATCH /campaigns/{id}/steps/{stepId}``."""
        return cast(
            Step,
            await self._client._request(
                "PATCH",
                f"/campaigns/{path_param(campaign_id)}/steps/{path_param(step_id)}",
                body=dict(params),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def delete(
        self,
        campaign_id: str,
        step_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> None:
        """``DELETE /campaigns/{id}/steps/{stepId}``."""
        await self._client._request(
            "DELETE",
            f"/campaigns/{path_param(campaign_id)}/steps/{path_param(step_id)}",
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=extra_headers,
        )


class AsyncCampaignLeads(_Resource):
    async def list(
        self,
        campaign_id: str,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **filters: Any,
    ) -> AsyncPage[Contact]:
        """Leads of one campaign (``POST /contacts/search`` with one campaign id).

        Each row carries ``campaign_lead``; ``page.raw["lead_counts"]`` has the
        per-status totals on the first page. Extra filters: ``lead_status``,
        ``engagement`` and any ``contacts.list`` filter.
        """
        return cast(
            "AsyncPage[Contact]",
            await self._client._get_page(
                "POST",
                "/contacts/search",
                query=_optional(cursor=cursor, limit=limit),
                body=_body(filters, campaign_ids=[campaign_id]),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def add(
        self,
        campaign_id: str,
        contacts: ContactsArg,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> List[Contact]:
        """Add contacts to a campaign (``POST /contacts`` with ``campaigns: [id]``).

        Can send mail: leads added to an active campaign are queued, and a
        completed campaign starts again on its own.
        """
        rows = [contacts] if isinstance(contacts, Mapping) else list(contacts)
        body: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            campaigns = list(item.get("campaigns") or [])
            if campaign_id not in campaigns:
                campaigns.append(campaign_id)
            item["campaigns"] = campaigns
            body.append(item)
        return cast(
            List[Contact],
            await self._client._request(
                "POST",
                "/contacts",
                body=body,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def get_hold(
        self, campaign_id: str, contact_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None
    ) -> LeadHoldResult:
        """``GET /campaigns/{id}/leads/{contactId}/hold``."""
        return cast(
            LeadHoldResult,
            await self._client._request(
                "GET",
                f"/campaigns/{path_param(campaign_id)}/leads/{path_param(contact_id)}/hold",
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def pause(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        until: Any = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> LeadHoldResult:
        """``POST /campaigns/{id}/leads/{contactId}/pause``. Omit ``until`` for a hold only a resume lifts."""
        return cast(
            LeadHoldResult,
            await self._client._request(
                "POST",
                f"/campaigns/{path_param(campaign_id)}/leads/{path_param(contact_id)}/pause",
                body=_optional(until=until, reason=reason),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def resume(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> LeadHoldResult:
        """``POST /campaigns/{id}/leads/{contactId}/resume``. On a finished campaign it can restart and send."""
        return cast(
            LeadHoldResult,
            await self._client._request(
                "POST",
                f"/campaigns/{path_param(campaign_id)}/leads/{path_param(contact_id)}/resume",
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )


class AsyncCampaigns(_Resource):
    steps: AsyncCampaignSteps
    leads: AsyncCampaignLeads

    def __init__(self, client: "AsyncAyInbox") -> None:
        super().__init__(client)
        self.steps = AsyncCampaignSteps(client)
        self.leads = AsyncCampaignLeads(client)

    async def list(
        self,
        *,
        q: Optional[str] = None,
        status: Optional[str] = None,
        folder: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> AsyncPage[Campaign]:
        """``GET /campaigns``. ``status`` is draft, active, paused or completed. Recommended ``limit``: 1 to 100."""
        return cast(
            "AsyncPage[Campaign]",
            await self._client._get_page(
                "GET",
                "/campaigns",
                query=_optional(q=q, status=status, folder=folder, cursor=cursor, limit=limit),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def get(self, campaign_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> Campaign:
        """``GET /campaigns/{id}``."""
        return cast(
            Campaign,
            await self._client._request(
                "GET", f"/campaigns/{path_param(campaign_id)}", timeout=timeout, extra_headers=extra_headers
            ),
        )

    async def create(
        self,
        *,
        name: str,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> Campaign:
        """``POST /campaigns``. Never sends mail.

        Any other create field goes in as a keyword (``daily_limit``, ``timezone``,
        ``email_tag_ids``, ``folder_ids``, ``senders``, ``steps``, ...).
        """
        return cast(
            Campaign,
            await self._client._request(
                "POST",
                "/campaigns",
                body=_body(params, name=name),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def update(
        self,
        campaign_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> Campaign:
        """``PATCH /campaigns/{id}``. Omitted fields are left alone; a keyword set to ``None`` is sent as JSON null
        (``start_date=None`` clears the start date).

        ``status="active"`` runs the start path and can send mail: it needs
        START_CAMPAIGNS or SEND_CAMPAIGNS as well as WRITE_CAMPAIGNS.
        """
        return cast(
            Campaign,
            await self._client._request(
                "PATCH",
                f"/campaigns/{path_param(campaign_id)}",
                body=dict(params),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def delete(
        self,
        campaign_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> None:
        """``DELETE /campaigns/{id}``. Permanent."""
        await self._client._request(
            "DELETE",
            f"/campaigns/{path_param(campaign_id)}",
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=extra_headers,
        )

    async def start(
        self,
        campaign_id: str,
        *,
        acknowledge_list_risk: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> CampaignStartResult:
        """``POST /campaigns/{id}/start``. Sends real mail. Needs START_CAMPAIGNS or SEND_CAMPAIGNS."""
        body = _optional(acknowledge_list_risk=acknowledge_list_risk)
        return cast(
            CampaignStartResult,
            await self._client._request(
                "POST",
                f"/campaigns/{path_param(campaign_id)}/start",
                body=body if body else NOT_GIVEN,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def pause(
        self,
        campaign_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> CampaignStopResult:
        """``POST /campaigns/{id}/stop``. The campaign must be active; it becomes paused. Sends nothing."""
        return cast(
            CampaignStopResult,
            await self._client._request(
                "POST",
                f"/campaigns/{path_param(campaign_id)}/stop",
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def duplicate(
        self,
        campaign_id: str,
        *,
        name: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> Campaign:
        """``POST /campaigns/{id}/duplicate``. Returns the new draft."""
        body = _optional(name=name)
        return cast(
            Campaign,
            await self._client._request(
                "POST",
                f"/campaigns/{path_param(campaign_id)}/duplicate",
                body=body if body else NOT_GIVEN,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def overview(self, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> CampaignsOverview:
        """``GET /campaigns-overview``: counts by status and folder."""
        return cast(
            CampaignsOverview,
            await self._client._request("GET", "/campaigns-overview", timeout=timeout, extra_headers=extra_headers),
        )


class AsyncContacts(_Resource):
    async def list(
        self,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        category: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **filters: Any,
    ) -> AsyncPage[Contact]:
        """``POST /contacts/search``. A read, safe to retry.

        Filters go in as keywords and are sent as the search body (``query``,
        ``campaign_ids``, ``subscribed``, ``sort_by``, ``reverse``, ...). The same
        body is resent on every page. ``page.raw["counts"]`` is on the first page.
        """
        return cast(
            "AsyncPage[Contact]",
            await self._client._get_page(
                "POST",
                "/contacts/search",
                query=_optional(cursor=cursor, limit=limit, category=category),
                body=dict(filters),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def get(
        self, contact_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None
    ) -> ContactDetail:
        """``GET /contacts/{id}``."""
        return cast(
            ContactDetail,
            await self._client._request(
                "GET", f"/contacts/{path_param(contact_id)}", timeout=timeout, extra_headers=extra_headers
            ),
        )

    async def create(
        self,
        contacts: ContactsArg,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> List[Contact]:
        """``POST /contacts``: one contact or a list of up to 10,240. Upserts by email.

        Always returns a list. Can send mail when a contact names an active or
        completed campaign.
        """
        body: Any = dict(contacts) if isinstance(contacts, Mapping) else [dict(c) for c in contacts]
        return cast(
            List[Contact],
            await self._client._request(
                "POST",
                "/contacts",
                body=body,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def update(
        self,
        contact_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> Contact:
        """``PATCH /contacts/{id}``. ``campaigns``, ``categories`` and ``custom_fields`` replace when sent."""
        return cast(
            Contact,
            await self._client._request(
                "PATCH",
                f"/contacts/{path_param(contact_id)}",
                body=dict(params),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def delete(
        self,
        contact_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> None:
        """``DELETE /contacts/{id}``."""
        await self._client._request(
            "DELETE",
            f"/contacts/{path_param(contact_id)}",
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=extra_headers,
        )

    async def bulk_delete(
        self,
        selection: Union[Sequence[str], Mapping[str, Any]],
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> None:
        """``DELETE /contacts``: a list of contact ids, or ``{"all": True, "filters": {...}, "exclude": [...]}``."""
        body: Any = dict(selection) if isinstance(selection, Mapping) else list(selection)
        await self._client._request(
            "DELETE",
            "/contacts",
            body=body,
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=extra_headers,
        )


class AsyncMailboxes(_Resource):
    async def list(
        self,
        *,
        q: Optional[str] = None,
        tag: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> AsyncPage[Mailbox]:
        """``GET /emails``: the connected mailboxes."""
        return cast(
            "AsyncPage[Mailbox]",
            await self._client._get_page(
                "GET",
                "/emails",
                query=_optional(q=q, tag=tag, cursor=cursor, limit=limit),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def get(self, mailbox_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> Mailbox:
        """``GET /emails/{id}``."""
        return cast(
            Mailbox,
            await self._client._request(
                "GET", f"/emails/{path_param(mailbox_id)}", timeout=timeout, extra_headers=extra_headers
            ),
        )

    async def get_sync(
        self, mailbox_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None
    ) -> MailboxSync:
        """``GET /emails/{id}/sync``: sync state and policy."""
        return cast(
            MailboxSync,
            await self._client._request(
                "GET", f"/emails/{path_param(mailbox_id)}/sync", timeout=timeout, extra_headers=extra_headers
            ),
        )


class AsyncUnibox(_Resource):
    async def list_threads(
        self,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        folder: Optional[str] = None,
        direction: Optional[str] = None,
        from_: Optional[str] = None,
        address: Optional[str] = None,
        subject: Optional[str] = None,
        unseen: Optional[bool] = None,
        awaiting_reply: Optional[bool] = None,
        campaign_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        email_id: Optional[str] = None,
        email_ids: Optional[Sequence[str]] = None,
        category_ids: Optional[Sequence[str]] = None,
        since: Any = None,
        until: Any = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **filters: Any,
    ) -> AsyncPage[MessagePreview]:
        """``GET /unibox``: one row per conversation. Other query filters go in as keywords."""
        query = _optional(
            cursor=cursor,
            limit=limit,
            folder=folder,
            direction=direction,
            address=address,
            subject=subject,
            unseen=unseen,
            awaiting_reply=awaiting_reply,
            campaign_id=campaign_id,
            contact_id=contact_id,
            email_id=email_id,
            email_ids=email_ids,
            category_ids=category_ids,
            since=since,
            until=until,
        )
        if from_ is not None:
            query["from"] = from_
        query.update(filters)
        return cast(
            "AsyncPage[MessagePreview]",
            await self._client._get_page("GET", "/unibox", query=query, timeout=timeout, extra_headers=extra_headers),
        )

    async def get_thread(
        self,
        thread_id: str,
        *,
        email_id: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> AsyncPage[MessagePreview]:
        """``GET /unibox/thread``: the messages of one thread, as previews. Read bodies with ``get_message``."""
        return cast(
            "AsyncPage[MessagePreview]",
            await self._client._get_page(
                "GET",
                "/unibox/thread",
                query=_optional(thread_id=thread_id, email_id=email_id, limit=limit, cursor=cursor),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def get_message(
        self, message_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None
    ) -> Message:
        """``GET /unibox/{id}``: one full message. Marks it read for an unrestricted caller."""
        return cast(
            Message,
            await self._client._request(
                "GET", f"/unibox/{path_param(message_id)}", timeout=timeout, extra_headers=extra_headers
            ),
        )

    async def unread_count(
        self, *, email_id: Optional[str] = None, timeout: TimeoutTypes = None, extra_headers: Headers = None
    ) -> UnreadCount:
        """``GET /unibox/count``."""
        return cast(
            UnreadCount,
            await self._client._request(
                "GET",
                "/unibox/count",
                query=_optional(email_id=email_id),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def reply(
        self,
        *,
        email_account_id: str,
        to: Sequence[str],
        subject: str,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> SendResult:
        """``POST /unibox/reply``. Sends real mail. Needs WRITE_UNIBOX.

        Other fields: body_html, body_plain, cc, bcc, in_reply_to, thread_id,
        send_mode, scheduled_at, forward_message_id. Pass an idempotency key.
        """
        return cast(
            SendResult,
            await self._client._request(
                "POST",
                "/unibox/reply",
                body=_body(params, email_account_id=email_account_id, to=list(to), subject=subject),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def list_drafts(self, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> DraftList:
        """``GET /unibox/drafts``: the caller's compose drafts (not paginated)."""
        return cast(
            DraftList,
            await self._client._request("GET", "/unibox/drafts", timeout=timeout, extra_headers=extra_headers),
        )

    async def save_draft(
        self,
        draft_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> SavedDraft:
        """``PUT /unibox/drafts/{id}``. ``draft_id`` is a UUID you generate. Never sends."""
        return cast(
            SavedDraft,
            await self._client._request(
                "PUT",
                f"/unibox/drafts/{path_param(draft_id)}",
                body=dict(params),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def delete_draft(
        self,
        draft_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> DeletedDraft:
        """``DELETE /unibox/drafts/{id}``. Deleting a missing draft is a no-op."""
        return cast(
            DeletedDraft,
            await self._client._request(
                "DELETE",
                f"/unibox/drafts/{path_param(draft_id)}",
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def list_agent_drafts(self, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> AgentDraftList:
        """``GET /unibox/agent-drafts``: AI reply drafts waiting for a person (not paginated)."""
        return cast(
            AgentDraftList,
            await self._client._request("GET", "/unibox/agent-drafts", timeout=timeout, extra_headers=extra_headers),
        )

    async def approve_agent_draft(
        self,
        draft_id: str,
        *,
        body: Optional[str] = None,
        acknowledge_flags: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> SendResult:
        """``POST /unibox/agent-drafts/{id}/approve``. Sends real mail.

        A flagged draft answers ``409 draft_flagged`` until ``acknowledge_flags=True``.
        """
        payload = _optional(body=body, acknowledge_flags=acknowledge_flags)
        return cast(
            SendResult,
            await self._client._request(
                "POST",
                f"/unibox/agent-drafts/{path_param(draft_id)}/approve",
                body=payload if payload else NOT_GIVEN,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def discard_agent_draft(
        self,
        draft_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> DiscardResult:
        """``POST /unibox/agent-drafts/{id}/discard``."""
        return cast(
            DiscardResult,
            await self._client._request(
                "POST",
                f"/unibox/agent-drafts/{path_param(draft_id)}/discard",
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )


class AsyncTemplates(_Resource):
    async def list(
        self, *, q: Optional[str] = None, timeout: TimeoutTypes = None, extra_headers: Headers = None
    ) -> TemplateList:
        """``GET /templates``: every reply template in one response (not paginated)."""
        return cast(
            TemplateList,
            await self._client._request(
                "GET", "/templates", query=_optional(q=q), timeout=timeout, extra_headers=extra_headers
            ),
        )

    async def get(self, template_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> Template:
        """``GET /templates/{id}``."""
        return cast(
            Template,
            await self._client._request(
                "GET", f"/templates/{path_param(template_id)}", timeout=timeout, extra_headers=extra_headers
            ),
        )

    async def create(
        self,
        *,
        name: str,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> Template:
        """``POST /templates``. Other fields: subject, body_html, body_plain."""
        return cast(
            Template,
            await self._client._request(
                "POST",
                "/templates",
                body=_body(params, name=name),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def update(
        self,
        template_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
        **params: Any,
    ) -> Template:
        """``PATCH /templates/{id}``."""
        return cast(
            Template,
            await self._client._request(
                "PATCH",
                f"/templates/{path_param(template_id)}",
                body=dict(params),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def delete(
        self,
        template_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> None:
        """``DELETE /templates/{id}``."""
        await self._client._request(
            "DELETE",
            f"/templates/{path_param(template_id)}",
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=extra_headers,
        )


class AsyncWebhooks(_Resource):
    verify_signature = staticmethod(_webhooks.verify_signature)
    construct_event = staticmethod(_webhooks.construct_event)

    async def list(self, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> WebhookList:
        """``GET /webhooks``: every endpoint plus the event type catalogue."""
        return cast(
            WebhookList, await self._client._request("GET", "/webhooks", timeout=timeout, extra_headers=extra_headers)
        )

    async def create(
        self,
        *,
        url: str,
        description: Optional[str] = None,
        event_types: Optional[Sequence[str]] = None,
        enabled: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> WebhookEndpointWithSecret:
        """``POST /webhooks``. The response holds ``secret``, shown only here and on rotate."""
        body = _optional(
            url=url,
            description=description,
            event_types=list(event_types) if event_types is not None else None,
            enabled=enabled,
        )
        return cast(
            WebhookEndpointWithSecret,
            await self._client._request(
                "POST",
                "/webhooks",
                body=body,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def update(
        self,
        webhook_id: str,
        *,
        url: str,
        description: Optional[str] = None,
        event_types: Optional[Sequence[str]] = None,
        enabled: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> WebhookEndpoint:
        """``PATCH /webhooks/{id}``. Replaces the endpoint: send the full desired state
        (an omitted ``enabled`` becomes true, ``event_types`` is overwritten)."""
        body = _optional(
            url=url,
            description=description,
            event_types=list(event_types) if event_types is not None else None,
            enabled=enabled,
        )
        return cast(
            WebhookEndpoint,
            await self._client._request(
                "PATCH",
                f"/webhooks/{path_param(webhook_id)}",
                body=body,
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def delete(
        self,
        webhook_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> None:
        """``DELETE /webhooks/{id}``."""
        await self._client._request(
            "DELETE",
            f"/webhooks/{path_param(webhook_id)}",
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=extra_headers,
        )

    async def rotate_secret(
        self,
        webhook_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> WebhookSecret:
        """``POST /webhooks/{id}/rotate-secret``. Returns the new secret once."""
        return cast(
            WebhookSecret,
            await self._client._request(
                "POST",
                f"/webhooks/{path_param(webhook_id)}/rotate-secret",
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def verify(
        self,
        webhook_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> WebhookVerifyResult:
        """``POST /webhooks/{id}/verify``: re-send the verification challenge.

        To check a delivery's signature, use ``verify_signature``.
        """
        return cast(
            WebhookVerifyResult,
            await self._client._request(
                "POST",
                f"/webhooks/{path_param(webhook_id)}/verify",
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def event_types(self, *, timeout: TimeoutTypes = None, extra_headers: Headers = None) -> EventTypeList:
        """``GET /webhooks/event-types``."""
        return cast(
            EventTypeList,
            await self._client._request("GET", "/webhooks/event-types", timeout=timeout, extra_headers=extra_headers),
        )

    async def list_deliveries(
        self,
        *,
        webhook_id: Optional[str] = None,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        endpoint_id: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> AsyncPage[Delivery]:
        """``GET /webhooks/deliveries``, or ``GET /webhooks/{id}/deliveries`` when ``webhook_id`` is given."""
        path = f"/webhooks/{path_param(webhook_id)}/deliveries" if webhook_id is not None else "/webhooks/deliveries"
        return cast(
            "AsyncPage[Delivery]",
            await self._client._get_page(
                "GET",
                path,
                query=_optional(
                    status=status, event_type=event_type, endpoint_id=endpoint_id, limit=limit, cursor=cursor
                ),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )


class AsyncAnalytics(_Resource):
    async def dashboard(
        self,
        *,
        period: Optional[str] = None,
        campaign_ids: Optional[Sequence[str]] = None,
        folder_ids: Optional[Sequence[str]] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> DashboardAnalytics:
        """``GET /analytics/dashboard``. ``period`` is 7d (default), 30d or 90d."""
        return cast(
            DashboardAnalytics,
            await self._client._request(
                "GET",
                "/analytics/dashboard",
                query=_optional(period=period, campaign_ids=campaign_ids, folder_ids=folder_ids),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def campaign(
        self,
        campaign_id: str,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> CampaignAnalytics:
        """``GET /analytics/campaigns/{id}``. ``from_`` and ``to`` bound the day range."""
        query = _optional(to=to)
        if from_ is not None:
            query["from"] = from_
        return cast(
            CampaignAnalytics,
            await self._client._request(
                "GET",
                f"/analytics/campaigns/{path_param(campaign_id)}",
                query=query,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def campaign_daily(
        self,
        campaign_id: str,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> DataList:
        """``GET /analytics/campaigns/{id}/daily``. Row shape is not pinned down; rows are dicts."""
        query = _optional(to=to)
        if from_ is not None:
            query["from"] = from_
        return cast(
            DataList,
            await self._client._request(
                "GET",
                f"/analytics/campaigns/{path_param(campaign_id)}/daily",
                query=query,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def accounts(
        self,
        *,
        email_ids: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> AsyncPage[Dict[str, Any]]:
        """``GET /analytics/accounts``: per-mailbox health and usage rows (dicts)."""
        return cast(
            "AsyncPage[Dict[str, Any]]",
            await self._client._get_page(
                "GET",
                "/analytics/accounts",
                query=_optional(email_ids=email_ids, limit=limit, cursor=cursor),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def account(
        self, mailbox_id: str, *, timeout: TimeoutTypes = None, extra_headers: Headers = None
    ) -> Dict[str, Any]:
        """``GET /analytics/accounts/{id}``: one mailbox's status detail (a dict)."""
        return cast(
            Dict[str, Any],
            await self._client._request(
                "GET", f"/analytics/accounts/{path_param(mailbox_id)}", timeout=timeout, extra_headers=extra_headers
            ),
        )


class AsyncSuppressions(_Resource):
    async def list(
        self,
        *,
        q: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> AsyncPage[Suppression]:
        """``GET /suppressions``."""
        return cast(
            "AsyncPage[Suppression]",
            await self._client._get_page(
                "GET",
                "/suppressions",
                query=_optional(q=q, limit=limit, cursor=cursor),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def add(
        self,
        entries: Sequence[Union[str, Mapping[str, Any]]],
        *,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> SuppressionAddResult:
        """``POST /suppressions``. Each entry is an address or domain string, or ``{"value": ..., "reason": ...}``."""
        rows = [{"value": e} if isinstance(e, str) else dict(e) for e in entries]
        return cast(
            SuppressionAddResult,
            await self._client._request(
                "POST",
                "/suppressions",
                body=_optional(entries=rows, reason=reason),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def remove(
        self,
        suppression_id: str,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> None:
        """``DELETE /suppressions/{id}``. Lets mail reach that recipient again."""
        await self._client._request(
            "DELETE",
            f"/suppressions/{path_param(suppression_id)}",
            idempotency_key=idempotency_key,
            timeout=timeout,
            extra_headers=extra_headers,
        )


class AsyncAiTools(_Resource):
    async def list(
        self,
        *,
        format: Optional[str] = None,
        toolsets: Optional[Sequence[str]] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> Dict[str, Any]:
        """``GET /ai/tools``: the tools this credential may call.

        ``format`` is ayinbox (default), openai, hermes or functions. ``data`` rows
        follow ``types.AiTool``.
        """
        return cast(
            Dict[str, Any],
            await self._client._request(
                "GET",
                "/ai/tools",
                query=_optional(format=format, toolsets=toolsets),
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )

    async def call(
        self,
        name: str,
        arguments: Optional[Mapping[str, Any]] = None,
        *,
        idempotency_key: Optional[str] = None,
        timeout: TimeoutTypes = None,
        extra_headers: Headers = None,
    ) -> AiToolCallResult:
        """``POST /ai/tools/{name}/call``. Paid tools also need ``idempotency_key`` inside ``arguments``.

        When ``result["data"]["untrusted"]`` is true the result holds text from
        people outside the workspace: fence it as data before giving it to a model.
        """
        return cast(
            AiToolCallResult,
            await self._client._request(
                "POST",
                f"/ai/tools/{path_param(name)}/call",
                body=dict(arguments or {}),
                idempotency_key=idempotency_key,
                timeout=timeout,
                extra_headers=extra_headers,
            ),
        )
