from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from core.text import is_valid_username, normalize_email, normalize_login, normalize_text, normalize_username


def _normalize_email(value: str) -> str:
    return normalize_email(value)


def _normalize_username(value: str) -> str:
    return normalize_username(value)


def _normalize_display_text(value: str) -> str:
    return normalize_text(value)


class Spot(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=2000)
    tags: List[str] = Field(default_factory=list)

    lat: float
    lon: float

    # Store images as base64 strings (later you can switch to URLs)
    images: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None

    @field_validator("created_at")
    @classmethod
    def default_now(cls, v):
        return v or datetime.now(UTC)


class ClientErrorReport(BaseModel):
    kind: str = Field(default="exception", max_length=40)
    source: str = Field(default="app", max_length=80)
    message: str = Field(default="", max_length=8000)
    exception_type: Optional[str] = Field(default=None, max_length=200)
    stacktrace: str = Field(default="", max_length=200000)
    context: Dict[str, Any] = Field(default_factory=dict)
    platform: Optional[str] = Field(default=None, max_length=200)
    python_version: Optional[str] = Field(default=None, max_length=200)
    created_at: Optional[datetime] = None

    @field_validator("created_at")
    @classmethod
    def default_now_report(cls, v):
        return v or datetime.now(UTC)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    display_name: Optional[str] = Field(default=None, max_length=120)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_register_username(cls, v: str) -> str:
        username = _normalize_username(v)
        if not is_valid_username(username):
            raise ValueError("Invalid username format")
        return username

    @field_validator("email", mode="before")
    @classmethod
    def normalize_register_email(cls, v: str) -> str:
        email = _normalize_email(v)
        if "@" not in email:
            raise ValueError("Invalid email format")
        return email

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_register_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _normalize_display_text(v)


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=40)
    email: Optional[str] = Field(default=None, min_length=5, max_length=200)
    display_name: Optional[str] = Field(default=None, max_length=120)
    bio: Optional[str] = Field(default=None, max_length=1200)
    avatar_image: Optional[str] = Field(default=None, max_length=5_000_000)
    social_accounts: Optional[Dict[str, str]] = Field(default=None)
    follow_requires_approval: Optional[bool] = None
    current_password: Optional[str] = Field(default=None, max_length=200)
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=200)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_profile_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        username = _normalize_username(v)
        if not is_valid_username(username):
            raise ValueError("Invalid username format")
        return username

    @field_validator("email", mode="before")
    @classmethod
    def normalize_profile_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        email = _normalize_email(v)
        if "@" not in email:
            raise ValueError("Invalid email format")
        return email

    @field_validator("display_name", "bio", "avatar_image", "current_password", mode="before")
    @classmethod
    def normalize_profile_text_fields(cls, v):
        if v is None:
            return None
        return _normalize_display_text(v)


class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    bio: str = ""
    avatar_image: str = ""
    social_accounts: Dict[str, str] = Field(default_factory=dict)
    follow_requires_approval: bool = False
    is_admin: bool = False
    account_status: str = ""
    account_status_reason: str = ""
    posting_timeout_until: Optional[datetime] = None
    active_strike_weight: int = 0
    recent_strike_count: int = 0
    created_at: datetime


class ModerationUserSummary(BaseModel):
    id: str
    username: str = ""
    display_name: str = ""
    email: str = ""
    is_admin: bool = False


class ModerationTargetPreview(BaseModel):
    id: str
    label: str = ""
    subtitle: str = ""
    body: str = ""
    owner_user_id: str = ""
    spot_id: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    moderation_status: str = ""


class SpotUpsertRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=2000)
    tags: List[str] = Field(default_factory=list)
    lat: float
    lon: float
    images: List[str] = Field(default_factory=list)
    visibility: Literal["public", "following", "invite_only", "personal"] = "public"
    invite_user_ids: List[str] = Field(default_factory=list)


class SpotPublic(BaseModel):
    id: str
    owner_id: str
    title: str
    description: str
    tags: List[str] = Field(default_factory=list)
    lat: float
    lon: float
    images: List[str] = Field(default_factory=list)
    visibility: Literal["public", "following", "invite_only", "personal"] = "public"
    invite_user_ids: List[str] = Field(default_factory=list)
    moderation_status: Literal["visible", "flagged", "hidden"] = "visible"
    created_at: datetime


class ShareRequest(BaseModel):
    message: str = Field(default="", max_length=300)


class SupportTicketRequest(BaseModel):
    category: Literal["bug", "feature", "complaint", "question", "other"] = "other"
    subject: str = Field(min_length=3, max_length=140)
    message: str = Field(min_length=10, max_length=6000)
    page: str = Field(default="", max_length=240)
    contact_email: Optional[str] = Field(default=None, max_length=200)
    allow_contact: bool = False
    technical_details: str = Field(default="", max_length=200000)


class SupportTicketPublic(BaseModel):
    id: str
    user_id: str
    category: Literal["bug", "feature", "complaint", "question", "other"] = "other"
    subject: str
    message: str
    page: str = ""
    contact_email: str = ""
    allow_contact: bool = False
    technical_details: str = ""
    status: Literal["open", "closed"] = "open"
    created_at: datetime


class ModerationReportCreateRequest(BaseModel):
    target_type: Literal["spot", "comment", "meetup", "meetup_comment", "user"]
    target_id: str = Field(min_length=1, max_length=120)
    reason: Literal["spam", "harassment", "explicit_content", "impersonation", "other"] = "other"
    details: str = Field(default="", max_length=3000)
    device_id: str = Field(default="", max_length=200)


class ModerationReportReviewRequest(BaseModel):
    status: Literal["upheld", "dismissed"]
    action: Literal["none", "hide_content", "ban_user"] = "none"
    severity: Literal["low", "medium", "high"] = "medium"
    admin_notes: str = Field(default="", max_length=3000)


class ModerationUserStatusRequest(BaseModel):
    account_status: Literal["active", "watch", "banned"]
    reason: str = Field(default="", max_length=1000)
    posting_timeout_until: Optional[datetime] = None


class ModerationReportPublic(BaseModel):
    id: str
    reporter_user_id: str
    reporter_device_id: str = ""
    target_type: Literal["spot", "comment", "meetup", "meetup_comment", "user"]
    target_id: str
    target_owner_user_id: str = ""
    reason: Literal["spam", "harassment", "explicit_content", "impersonation", "other"] = "other"
    details: str = ""
    status: Literal["open", "upheld", "dismissed"] = "open"
    severity: str = ""
    action_taken: str = ""
    admin_notes: str = ""
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: str = ""
    reporter_user: Optional[ModerationUserSummary] = None
    target_owner_user: Optional[ModerationUserSummary] = None
    target_user: Optional[ModerationUserSummary] = None
    target_preview: Optional[ModerationTargetPreview] = None
    target_distinct_reporter_count: int = 0
    target_report_count: int = 0
    reporter_distinct_target_count: int = 0


class ModerationNotificationPublic(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    details: str = ""
    created_at: datetime


class ModerationUserPublic(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    account_status: Literal["active", "watch", "banned"] = "active"
    account_status_reason: str = ""
    posting_timeout_until: Optional[datetime] = None
    active_strike_weight: int = 0
    recent_strike_count: int = 0
    created_at: datetime


class FollowRequestPublic(BaseModel):
    follower: UserPublic
    created_at: datetime


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class LoginRequest(BaseModel):
    username_or_email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("username_or_email", mode="before")
    @classmethod
    def normalize_username_or_email(cls, v: str) -> str:
        return normalize_login(v)


class AuthUserRecord(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    email: str = Field(min_length=5, max_length=200)
    password_hash: str = Field(min_length=1, max_length=500)
    display_name: str = Field(min_length=1, max_length=120)
    bio: str = Field(default="", max_length=1200)
    avatar_image: str = Field(default="", max_length=5_000_000)
    social_accounts: Dict[str, str] = Field(default_factory=dict)
    follow_requires_approval: bool = False
    is_admin: bool = Field(default=False)
    account_status: Literal["active", "watch", "banned"] = "active"
    account_status_reason: str = Field(default="", max_length=1000)
    posting_timeout_until: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        username = _normalize_username(v)
        if not is_valid_username(username):
            raise ValueError("Invalid username format")
        return username

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        email = _normalize_email(v)
        if "@" not in email:
            raise ValueError("Invalid email format")
        return email

    @field_validator("display_name", "bio", "avatar_image", "account_status_reason", mode="before")
    @classmethod
    def normalize_user_text_fields(cls, v):
        return _normalize_display_text(v)

    @field_validator("social_accounts")
    @classmethod
    def sanitize_social_accounts(cls, v: Dict[str, str]) -> Dict[str, str]:
        out: Dict[str, str] = {}
        source = v if isinstance(v, dict) else {}
        for key, value in source.items():
            k = normalize_text(key)
            val = normalize_text(value)
            if not k or not val:
                continue
            if len(k) > 40 or len(val) > 500:
                continue
            out[k] = val
        return out

    @field_validator("created_at")
    @classmethod
    def default_created_at(cls, v):
        return v or datetime.now(UTC)


class FavoriteRef(BaseModel):
    spot_id: str
    created_at: datetime


class FollowRef(BaseModel):
    user_id: str
    created_at: datetime


class FollowRequestRef(BaseModel):
    follower_id: str
    created_at: datetime


class BlockRef(BaseModel):
    user_id: str
    created_at: datetime


class SpotComment(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    spot_id: str
    user_id: str
    message: str = Field(min_length=1, max_length=2000)
    moderation_status: Literal["visible", "flagged", "hidden"] = "visible"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}

    @field_validator("created_at")
    @classmethod
    def default_created_at(cls, v):
        return v or datetime.now(UTC)


class CommentCreateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class CommentUpdateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class MeetupCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=3000)
    starts_at: datetime
    invite_user_ids: List[str] = Field(default_factory=list)
    spot_id: Optional[str] = Field(default=None, max_length=50)


class MeetupUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=3000)
    starts_at: Optional[datetime] = None
    invite_user_ids: Optional[List[str]] = None
    spot_id: Optional[str] = Field(default=None, max_length=50)


class MeetupPublic(BaseModel):
    id: str
    host_user_id: str
    title: str
    description: str = ""
    starts_at: datetime
    invite_user_ids: List[str] = Field(default_factory=list)
    spot_id: Optional[str] = None
    spot: Optional[SpotPublic] = None
    moderation_status: Literal["visible", "flagged", "hidden"] = "visible"
    created_at: datetime
    updated_at: datetime


class MeetupInviteRef(BaseModel):
    meetup_id: str
    user_id: str
    status: Literal["pending", "accepted", "declined"] = "pending"
    response_comment: str = ""
    created_at: datetime
    responded_at: Optional[datetime] = None


class MeetupRespondRequest(BaseModel):
    status: Literal["accepted", "declined"]
    comment: str = Field(default="", max_length=1000)


class MeetupComment(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    meetup_id: str
    user_id: str
    message: str = Field(min_length=1, max_length=2000)
    moderation_status: Literal["visible", "flagged", "hidden"] = "visible"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}

    @field_validator("created_at")
    @classmethod
    def default_meetup_comment_created_at(cls, v):
        return v or datetime.now(UTC)


class MeetupCommentCreateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class MeetupCommentUpdateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class MeetupNotificationPublic(BaseModel):
    id: str
    user_id: str
    meetup_id: str
    meetup_title: str
    notification_type: str
    from_user_id: str
    from_username: str
    message: str = ""
    created_at: datetime

