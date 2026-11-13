"""Response and request shapes.

Every response is a plain ``dict``; these ``TypedDict``s describe the fields the
API documents. All of them are ``total=False``: a field can be missing, and
fields the API adds later stay in the dict. Shapes the API does not pin down
are typed as ``Dict[str, Any]``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

__all__ = [
    "Identity",
    "Pagination",
    "ScheduleWindow",
    "CampaignSender",
    "Campaign",
    "CampaignStartResult",
    "CampaignStopResult",
    "CampaignsOverview",
    "FolderCount",
    "Step",
    "StepInput",
    "LeadHold",
    "LeadHoldResult",
    "ContactCampaignRef",
    "ContactLabel",
    "ContactCampaignProgress",
    "Contact",
    "ContactDetail",
    "ContactInput",
    "CustomFieldFilter",
    "Mailbox",
    "SyncState",
    "SyncPolicy",
    "SyncFolder",
    "MailboxSync",
    "UniboxLabel",
    "MessagePreview",
    "Message",
    "UnreadCount",
    "SendResult",
    "ComposeDraft",
    "DraftList",
    "SavedDraft",
    "DeletedDraft",
    "AgentDraft",
    "AgentDraftList",
    "DiscardResult",
    "Template",
    "TemplateList",
    "WebhookEndpoint",
    "WebhookEndpointWithSecret",
    "EventType",
    "WebhookList",
    "EventTypeList",
    "WebhookSecret",
    "WebhookVerifyResult",
    "Delivery",
    "WebhookEvent",
    "DashboardStats",
    "DashboardAnalytics",
    "CampaignAnalyticsSummary",
    "CampaignAnalytics",
    "DataList",
    "Suppression",
    "SuppressionEntry",
    "SuppressionAddResult",
    "AiTool",
    "AiToolCall",
    "AiToolCallResult",
]


class Identity(TypedDict, total=False):
    user_id: str
    email: str
    name: str
    first_name: str
    last_name: str
    organization_id: str
    organization_name: str
    auth_type: str
    scopes: List[str]


class Pagination(TypedDict, total=False):
    next_cursor: Optional[str]
    has_more: bool
    total: Optional[int]


class ScheduleWindow(TypedDict, total=False):
    start: int
    end: int


class CampaignSender(TypedDict, total=False):
    email_account_id: str
    weight: int
    enabled: bool
    last_sent_at: str


class Campaign(TypedDict, total=False):
    id: str
    user_id: str
    organization_id: str
    name: str
    description: str
    status: str
    stop_on_reply: bool
    stop_on_meeting: bool
    open_tracking: bool
    link_tracking: bool
    text_only: bool
    unsubscribe_header: bool
    risky_emails: bool
    daily_limit: int
    unsubscribe_mode: str
    cc: List[str]
    bcc: List[str]
    start_date: Optional[str]
    end_date: Optional[str]
    timezone: str
    effective_timezone: str
    days: int
    start_time: str
    end_time: str
    schedule_windows: List[List[ScheduleWindow]]
    email_tags: List[str]
    folders: List[str]
    contact_order_by: str
    contact_order_dir: str
    contact_order_field: str
    sender_strategy: str
    rotation_mode: str
    senders: List[CampaignSender]
    ramp_enabled: bool
    ramp_start: int
    ramp_increment: int
    ramp_ceiling: int
    ramp_level: int
    ramp_level_date: str
    esp_match_mode: str
    max_new_leads_per_day: int
    prioritize_new_leads: bool
    continuous: bool
    review_first_emails: bool
    entry_delay_minutes: int
    idle_since: str
    guardrail_enabled: bool
    guardrail_bounce_rate_max: float
    guardrail_complaint_rate_max: float
    guardrail_reply_rate_min: float
    guardrail_min_sample: int
    guardrail_window_days: int
    guardrail_tripped_at: str
    guardrail_reason: str
    tracking_domain: str
    tracking_domain_verified: bool
    tracking_domain_verified_at: str
    utm_tracking: bool
    utm_source: str
    utm_medium: str
    utm_campaign: str
    last_status_change_at: str
    created_at: str
    updated_at: str


class CampaignStartResult(TypedDict, total=False):
    status: str
    waiting_for_leads: bool


class CampaignStopResult(TypedDict, total=False):
    status: str


class FolderCount(TypedDict, total=False):
    folder_id: str
    total: int


class CampaignsOverview(TypedDict, total=False):
    total: int
    active: int
    paused: int
    draft: int
    completed: int
    folders: List[FolderCount]


class Step(TypedDict, total=False):
    id: str
    name: str
    subject: str
    body_plain: str
    body_html: str
    body_sync: bool
    body_code: bool
    wait_after: int
    position: int
    thread_reply: bool
    x: float
    y: float
    conditions: Dict[str, Any]
    kind: str
    action: Dict[str, Any]
    created_at: str
    updated_at: str


class StepInput(TypedDict, total=False):
    name: str
    subject: str
    body_plain: str
    body_html: str
    body_sync: bool
    body_code: bool
    wait_after: int
    thread_reply: bool


class LeadHold(TypedDict, total=False):
    since: str
    until: str
    reason: str
    source: str


class LeadHoldResult(TypedDict, total=False):
    campaign_id: str
    contact_id: str
    hold: LeadHold


class ContactCampaignRef(TypedDict, total=False):
    id: str
    name: str


class ContactLabel(TypedDict, total=False):
    id: str
    title: str
    color: str


class ContactCampaignProgress(TypedDict, total=False):
    status: str
    sent: int
    opened: int
    machine_opened: int
    clicked: int
    replied: int
    bounced: int
    last_activity_at: str
    current_step: str
    failure_reason: str
    sender: str
    hold: LeadHold
    cc: List[Any]


class Contact(TypedDict, total=False):
    id: str
    first_name: str
    last_name: str
    email: str
    company: str
    phone: str
    custom_fields: Dict[str, str]
    subscribed: bool
    campaigns: List[ContactCampaignRef]
    categories: List[ContactLabel]
    verification_status: str
    verification_reason: str
    is_catch_all: bool
    verification_checked_at: str
    verification_source: str
    verification_provider: str
    verification_sub_status: str
    verification_confidence: int
    verification_requested_at: str
    mail_host: str
    esp_provider: str
    esp_resolved_at: str
    consent_given_at: str
    consent_source: str
    lead_score: Dict[str, Any]
    campaign_lead: ContactCampaignProgress
    outreach: Dict[str, Any]
    created_at: str
    updated_at: str


class ContactDetail(Contact, total=False):
    engagement: Dict[str, Any]
    suppression: Dict[str, Any]
    verification: Dict[str, Any]
    source: str
    source_detail: str
    first_seen_at: str
    consent_country: str
    consent_required: bool


class ContactInput(TypedDict, total=False):
    """One contact for ``contacts.create``. ``email`` is required."""

    email: str
    first_name: str
    last_name: str
    company: str
    phone: str
    campaigns: List[str]
    categories: List[str]
    segments: List[str]
    custom_fields: Dict[str, str]
    subscribed: bool
    verification_status: str
    verification_provider: str


class CustomFieldFilter(TypedDict, total=False):
    name: str
    value: str
    type: str


class Mailbox(TypedDict, total=False):
    id: str
    user_id: str
    organization_id: str
    worker_id: Optional[str]
    email: str
    name: str
    signature_plain: str
    signature_html: str
    send_as_email: str
    provider: str
    status: str
    mail_host: str
    auth_method: str
    avatar_url: str
    last_synced_at: str
    campaign_limit: int
    min_wait_time: int
    reply_to: str
    tracking_domain: str
    tracking_domain_verified: bool
    auth_state: str
    auth_spf: bool
    auth_dkim: bool
    auth_dmarc: bool
    auth_checked_at: str
    warmup: Optional[str]
    warmup_paused_at: Optional[str]
    warmup_base: int
    warmup_max: int
    warmup_increase: int
    warmup_reply_rate: int
    warmup_pool_type: str
    timezone: str
    save_to_sent: bool
    relay_folder_moves: bool
    tags: List[str]
    created_at: str
    updated_at: str


class SyncState(TypedDict, total=False):
    backfill_status: str
    backfill_cursor: Any
    backfill_synced: int
    backfill_since: str
    backfill_started_at: str
    backfill_completed_at: str
    throttled_until: str
    throttle_reason: str
    deferred: int
    last_synced_at: str


class SyncPolicy(TypedDict, total=False):
    backfill_days: int
    backfill_messages: int
    daily_messages: int
    org_daily_messages: int
    skip_folders: List[str]


class SyncFolder(TypedDict, total=False):
    name: str
    folder: str


class MailboxSync(TypedDict, total=False):
    state: Optional[SyncState]
    policy: SyncPolicy
    skip_folders: List[str]
    folders: List[SyncFolder]


class UniboxLabel(TypedDict, total=False):
    id: str
    title: str
    color: str


class MessagePreview(TypedDict, total=False):
    id: str
    email_id: str
    thread_id: str
    from_addr: List[str]
    to_addr: List[str]
    subject: str
    snippet: str
    internal_date: str
    seen: bool
    message_count: int
    has_unread: bool
    labels: List[UniboxLabel]
    answers_mailbox_id: str
    campaign_id: str


# Functional form: "from" is a Python keyword and "ReplyTo" is capitalised on the wire.
Message = TypedDict(
    "Message",
    {
        "id": str,
        "gmail_id": str,
        "uid": int,
        "email_id": str,
        "folder": str,
        "parent_id": str,
        "thread_id": str,
        "flags": List[str],
        "bcc": List[str],
        "cc": List[str],
        "date": str,
        "from": List[str],
        "in_reply_to": List[str],
        "message_id": str,
        "ReplyTo": List[str],
        "to": List[str],
        "subject": str,
        "size": int,
        "internal_date": str,
        "mod_seq": int,
        "body_plain": str,
        "body_html": str,
        "body_truncated": bool,
    },
    total=False,
)


class UnreadCount(TypedDict, total=False):
    count: int


class SendResult(TypedDict, total=False):
    task_id: str
    scheduled_at: str
    send_mode: str


class ComposeDraft(TypedDict, total=False):
    id: str
    email_account_id: str
    to: List[str]
    cc: List[str]
    bcc: List[str]
    subject: str
    body: str
    body_html: str
    created_at: str
    updated_at: str


class DraftList(TypedDict, total=False):
    data: List[ComposeDraft]


class SavedDraft(TypedDict, total=False):
    id: str


class DeletedDraft(TypedDict, total=False):
    deleted: bool


class AgentDraft(TypedDict, total=False):
    id: str
    organization_id: str
    email_account_id: str
    owner_user_id: str
    thread_id: str
    source_message_id: str
    contact_id: str
    campaign_id: str
    to_addr: str
    subject: str
    in_reply_to: str
    body: str
    intent_class: str
    confidence: float
    model: str
    status: str
    grounding: Dict[str, Any]
    created_at: str
    updated_at: str


class AgentDraftList(TypedDict, total=False):
    data: List[AgentDraft]


class DiscardResult(TypedDict, total=False):
    status: str


class Template(TypedDict, total=False):
    id: str
    organization_id: str
    user_id: str
    name: str
    subject: str
    body_html: str
    body_plain: str
    position: int
    created_at: str
    updated_at: str


class TemplateList(TypedDict, total=False):
    data: List[Template]


class WebhookEndpoint(TypedDict, total=False):
    id: str
    organization_id: str
    url: str
    description: str
    event_types: List[str]
    enabled: bool
    last_success_at: str
    last_failure_at: str
    last_failure_reason: str
    consecutive_failures: int
    oauth_application_id: str
    created_by: str
    verified_at: str
    ownership_confirmed: bool
    auto_disabled_at: str
    disabled_reason: str
    created_at: str
    updated_at: str


class WebhookEndpointWithSecret(WebhookEndpoint, total=False):
    secret: str


class EventType(TypedDict, total=False):
    type: str
    category: str
    description: str
    firehose: bool
    deprecated: bool


class WebhookList(TypedDict, total=False):
    endpoints: List[WebhookEndpoint]
    event_types: List[EventType]


class EventTypeList(TypedDict, total=False):
    event_types: List[EventType]


class WebhookSecret(TypedDict, total=False):
    secret: str


class WebhookVerifyResult(TypedDict, total=False):
    status: str


class Delivery(TypedDict, total=False):
    id: str
    endpoint_id: str
    organization_id: str
    event_type: str
    event_id: str
    payload: Dict[str, Any]
    status: str
    attempt_count: int
    max_attempts: int
    next_attempt_at: str
    last_attempt_at: str
    response_status: int
    response_body_excerpt: str
    error_reason: str
    created_at: str
    updated_at: str


class WebhookEvent(TypedDict, total=False):
    id: str
    event_type: str
    organization_id: str
    created_at: str
    data: Dict[str, Any]


class DashboardStats(TypedDict, total=False):
    total_emails_sent: int
    total_opens: int
    machine_opens: int
    total_clicks: int
    machine_clicks: int
    total_replies: int
    total_bounces: int
    open_rate: float
    click_rate: float
    reply_rate: float
    bounce_rate: float
    active_campaigns: int
    active_accounts: int


class DashboardAnalytics(TypedDict, total=False):
    period: str
    overall_stats: DashboardStats
    recent_activity: List[Dict[str, Any]]
    top_campaigns: List[Dict[str, Any]]
    account_health: Dict[str, Any]
    daily_trend: List[Dict[str, Any]]
    capacity_today: Dict[str, Any]
    scope: Dict[str, Any]


class CampaignAnalyticsSummary(TypedDict, total=False):
    total_contacts: int
    emails_sent: int
    emails_pending: int
    unique_opens: int
    machine_opens: int
    unique_clicks: int
    machine_clicks: int
    replies: int
    positive_replies: int
    interested_leads: int
    bounces: int
    unsubscribes: int


class CampaignAnalytics(TypedDict, total=False):
    campaign_id: str
    name: str
    status: str
    date_range: Dict[str, Any]
    summary: CampaignAnalyticsSummary
    steps: List[Dict[str, Any]]
    daily_stats: List[Dict[str, Any]]
    engagement: Dict[str, Any]


class DataList(TypedDict, total=False):
    data: List[Dict[str, Any]]


class Suppression(TypedDict, total=False):
    id: str
    organization_id: str
    email: str
    kind: str
    reason: str
    source: str
    campaign_id: str
    expires_at: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class SuppressionEntry(TypedDict, total=False):
    value: str
    reason: str


class SuppressionAddResult(TypedDict, total=False):
    added: int
    skipped: List[str]


class AiTool(TypedDict, total=False):
    """A tool row. ``format="ayinbox"`` fills name/description/input_schema; other formats fill type/function."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    type: str
    function: Dict[str, Any]


class AiToolCall(TypedDict, total=False):
    name: str
    result: Any
    result_text: str
    untrusted: bool


class AiToolCallResult(TypedDict, total=False):
    data: AiToolCall
