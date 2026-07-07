from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any, Callable

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from core.admin_setup import is_admin_user
from core.text import normalize_email, normalize_search_text, normalize_username
from models.schemas import (
    BlockRef,
    CommentCreateRequest,
    CommentUpdateRequest,
    FavoriteRef,
    FollowRef,
    FollowRequestRef,
    MeetupNotificationPublic,
    ModerationNotificationPublic,
    ModerationReportCreateRequest,
    ModerationReportPublic,
    ModerationReportReviewRequest,
    ModerationUserPublic,
    ModerationUserStatusRequest,
    MeetupComment,
    MeetupCommentCreateRequest,
    MeetupCommentUpdateRequest,
    MeetupCreateRequest,
    MeetupInviteRef,
    MeetupPublic,
    MeetupRespondRequest,
    MeetupUpdateRequest,
    ShareRequest,
    SpotComment,
    SpotPublic,
    SpotUpsertRequest,
    SupportTicketPublic,
    SupportTicketRequest,
    UpdateProfileRequest,
    UserPublic,
)
from services.auth.password_service import password_service

from .ids import as_text, normalize_login, normalize_social_accounts, parse_object_id, safe_user_projection, serialize_id, spot_document_by_id, viewer_user_id
from .indexes import ensure_indexes
from .mappers import to_meetup_notification_public, to_meetup_public, to_moderation_notification_public
from .mappers import to_moderation_user_public, to_spot_public
from .mappers import to_user_public
from .policies import can_view_private_user, can_view_spot, is_blocked_pair, is_following
from .favorite_workflows import FavoriteWorkflowExecutor
from .comment_actions import SocialCommentActions
from .meetup_actions import SocialMeetupActions
from .moderation_actions import SocialModerationActions
from .moderation_support import SocialModerationSupport
from .profile_actions import SocialProfileActions
from .relationship_actions import SocialRelationshipActions
from .spot_workflows import SpotWorkflowExecutor
from .support_actions import SocialSupportActions


def normalize_invite_status(value: Any) -> str:
    text = as_text(value).lower()
    if text in {"pending", "accepted", "declined"}:
        return text
    return "pending"


class SocialActions:
    def __init__(self, repos) -> None:
        self.repos = repos
        self.dto_types = {
            "block": BlockRef,
            "follow": FollowRef,
            "follow_request": FollowRequestRef,
        }
        self.spot_workflows = SpotWorkflowExecutor(self)
        self.favorite_workflows = FavoriteWorkflowExecutor(self)
        self.profile_actions = SocialProfileActions(self)
        self.relationship_actions = SocialRelationshipActions(self)
        self.support_actions = SocialSupportActions(self)
        self.moderation_actions = SocialModerationActions(self)
        self.moderation_support = SocialModerationSupport(self)
        self.comment_actions = SocialCommentActions(self)
        self.meetup_actions = SocialMeetupActions(self)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _content_status(doc: dict[str, Any]) -> str:
        text = as_text(doc.get("moderation_status") or "visible").lower()
        if text in {"visible", "flagged", "hidden"}:
            return text
        return "visible"

    def is_admin(self, current_user: dict[str, Any] | None) -> bool:
        return is_admin_user(current_user)

    def _can_view_content_doc(self, doc: dict[str, Any], current_user: dict[str, Any] | None) -> bool:
        if self.is_admin(current_user):
            return True
        return self._content_status(doc) != "hidden"

    def _posting_timeout_until(self, user_doc: dict[str, Any]) -> datetime | None:
        value = user_doc.get("posting_timeout_until")
        return value if isinstance(value, datetime) else None

    def ensure_can_post(self, current_user: dict[str, Any]) -> None:
        if self.is_admin(current_user):
            return
        timeout_until = self._posting_timeout_until(current_user)
        now = self._now()
        if timeout_until and timeout_until > now:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Posting is temporarily restricted until {timeout_until.isoformat()}",
            )

    def _notify_user(self, user_id: str, *, title: str, message: str, details: str = "") -> None:
        self.moderation_support.notify_user(user_id, title=title, message=message, details=details)

    def _notify_meetup(
        self,
        user_id: str,
        *,
        meetup_id: str,
        meetup_title: str,
        notification_type: str,
        from_user_id: str,
        from_username: str,
        message: str = "",
    ) -> None:
        uid = as_text(user_id)
        if not uid:
            return
        self.repos.meetup_notifications.insert_one(
            {
                "user_id": uid,
                "meetup_id": as_text(meetup_id),
                "meetup_title": as_text(meetup_title),
                "notification_type": as_text(notification_type),
                "from_user_id": as_text(from_user_id),
                "from_username": as_text(from_username),
                "message": as_text(message),
                "created_at": self._now(),
            }
        )

    @staticmethod
    def _user_summary(self, user_id: str) -> dict[str, Any] | None:
        return self.moderation_support.user_summary(user_id)

    def _reported_person_id(self, row: dict[str, Any]) -> str:
        return self.moderation_support.reported_person_id(row)

    def _moderation_report_metrics(self, row: dict[str, Any]) -> tuple[int, int, int]:
        return self.moderation_support.moderation_report_metrics(row)

    def _moderation_report_public(self, row: dict[str, Any]) -> ModerationReportPublic:
        return self.moderation_support.moderation_report_public(row)

    def _recalculate_posting_timeout(self, user_id: str) -> tuple[datetime | None, str]:
        return self.moderation_support.recalculate_posting_timeout(user_id)

    def me_id(self, current_user: dict[str, Any] | None) -> str:
        return viewer_user_id(current_user)

    def user_or_404(self, user_id: str) -> tuple[str, dict[str, Any]]:
        target_oid = parse_object_id(user_id)
        target = self.repos.users.find_one({"_id": target_oid}, safe_user_projection())
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return serialize_id(target_oid), target

    def require_private_profile_access(self, target_user: dict[str, Any], current_user: dict[str, Any]) -> str:
        me_id = self.me_id(current_user)
        if self.is_admin(current_user):
            return me_id
        if not can_view_private_user(self.repos, target_user, me_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile is private")
        return me_id

    def spot_or_404(self, spot_id: str) -> dict[str, Any]:
        spot = spot_document_by_id(self.repos, spot_id)
        if not spot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")
        return spot

    def require_spot_visible(self, spot: dict[str, Any], current_user: dict[str, Any], detail: str) -> str:
        me_id = self.me_id(current_user)
        if self.is_admin(current_user):
            return me_id
        if self._content_status(spot) == "hidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        if not can_view_spot(self.repos, me_id, spot):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        return me_id

    def comment_or_404(self, comment_id: str) -> dict[str, Any]:
        if not ObjectId.is_valid(comment_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid comment ID")
        row = self.repos.comments.find_one({"_id": ObjectId(comment_id)})
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        return row

    def meetup_or_404(self, meetup_id: str) -> dict[str, Any]:
        if not ObjectId.is_valid(meetup_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid meetup ID")
        row = self.repos.meetups.find_one({"_id": ObjectId(meetup_id)})
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meetup not found")
        return row

    def can_access_meetup(self, meetup: dict[str, Any], user_id: str) -> bool:
        if user_id and ObjectId.is_valid(user_id):
            current_user = self.repos.users.find_one({"_id": ObjectId(user_id)})
            if current_user and self.is_admin(current_user):
                return True
        if self._content_status(meetup) == "hidden":
            return False
        host_id = as_text(meetup.get("host_user_id"))
        if host_id and host_id == user_id:
            return True
        meetup_id = serialize_id(meetup.get("_id"))
        invite = self.repos.meetup_invites.find_one({"meetup_id": meetup_id, "user_id": user_id})
        return bool(invite)

    def sorted_rows(self, repository, query: dict[str, Any], limit: int) -> list[dict[str, Any]]:
        return repository.find_many_sorted(query, sort_field="created_at", sort_direction=-1, limit=limit)

    def map_relation_refs(
        self,
        rows: list[dict[str, Any]],
        *,
        source_field: str,
        dto_type,
        dto_id_field: str,
        allow_id: Callable[[str], bool] | None = None,
    ) -> list[Any]:
        out = []
        for row in rows:
            related_id = as_text(row.get(source_field))
            if not related_id:
                continue
            if allow_id and not allow_id(related_id):
                continue
            out.append(dto_type(**{dto_id_field: related_id, "created_at": row.get("created_at") or datetime.now(UTC)}))
        return out

    def insert_relation_ignore_duplicate(self, repository, document: dict[str, Any]) -> None:
        try:
            repository.insert_one(document)
        except DuplicateKeyError:
            pass

    def upsert_relation_timestamp(self, repository, query: dict[str, Any]) -> None:
        repository.update_fields(query, {"created_at": datetime.now(UTC)}, upsert=True)

    def delete_relation_pair(self, repository, left_field: str, left_id: str, right_field: str, right_id: str) -> None:
        repository.delete_one_by_query({left_field: left_id, right_field: right_id})

    def delete_bidirectional_relation_pairs(self, repository, left_field: str, left_id: str, right_field: str, right_id: str) -> None:
        repository.delete_many({"$or": [{left_field: left_id, right_field: right_id}, {left_field: right_id, right_field: left_id}]})

    def get_me(self, current_user: dict[str, Any]) -> UserPublic:
        return self.profile_actions.get_me(current_user)

    def update_me(self, req: UpdateProfileRequest, current_user: dict[str, Any]) -> UserPublic:
        return self.profile_actions.update_me(req, current_user)

    def search_users(self, query: str, limit: int, current_user: dict[str, Any]) -> list[UserPublic]:
        return self.profile_actions.search_users(query, limit, current_user)

    def get_user_profile(self, user_id: str, current_user: dict[str, Any] | None) -> UserPublic:
        return self.profile_actions.get_user_profile(user_id, current_user)

    def list_visible_spots(self, current_user: dict[str, Any] | None) -> list[SpotPublic]:
        return self.spot_workflows.list_visible_spots(current_user)

    def create_spot(self, req: SpotUpsertRequest, current_user: dict[str, Any]) -> SpotPublic:
        return self.spot_workflows.create_spot(req, current_user)

    def update_spot(self, spot_id: str, req: SpotUpsertRequest, current_user: dict[str, Any]) -> SpotPublic:
        return self.spot_workflows.update_spot(spot_id, req, current_user)

    def delete_spot(self, spot_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.spot_workflows.delete_spot(spot_id, current_user)

    def user_spots(self, user_id: str, current_user: dict[str, Any]) -> list[SpotPublic]:
        return self.spot_workflows.user_spots(user_id, current_user)

    def add_favorite(self, spot_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.favorite_workflows.add_favorite(spot_id, current_user)

    def remove_favorite(self, spot_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.favorite_workflows.remove_favorite(spot_id, current_user)

    def list_favorites(self, current_user: dict[str, Any]) -> list[FavoriteRef]:
        return self.favorite_workflows.list_favorites(current_user)

    def user_favorites(self, user_id: str, current_user: dict[str, Any]) -> list[FavoriteRef]:
        return self.favorite_workflows.user_favorites(user_id, current_user)

    def follow_requests(self, current_user: dict[str, Any]) -> list[FollowRequestRef]:
        return self.relationship_actions.follow_requests(current_user)

    def approve_follow_request(self, follower_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.relationship_actions.approve_follow_request(follower_id, current_user)

    def reject_follow_request(self, follower_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.relationship_actions.reject_follow_request(follower_id, current_user)

    def follow_user(self, user_id: str, current_user: dict[str, Any]) -> dict[str, str | bool]:
        return self.relationship_actions.follow_user(user_id, current_user)

    def unfollow_user(self, user_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.relationship_actions.unfollow_user(user_id, current_user)

    def followers(self, user_id: str, current_user: dict[str, Any]) -> list[FollowRef]:
        return self.relationship_actions.followers(user_id, current_user)

    def following(self, user_id: str, current_user: dict[str, Any]) -> list[FollowRef]:
        return self.relationship_actions.following(user_id, current_user)

    def remove_follower(self, user_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.relationship_actions.remove_follower(user_id, current_user)

    def block_user(self, user_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.relationship_actions.block_user(user_id, current_user)

    def unblock_user(self, user_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.relationship_actions.unblock_user(user_id, current_user)

    def blocked_users(self, current_user: dict[str, Any]) -> list[BlockRef]:
        return self.relationship_actions.blocked_users(current_user)

    def share_spot(self, spot_id: str, req: ShareRequest, current_user: dict[str, Any]) -> dict[str, bool]:
        spot = self.spot_or_404(spot_id)
        me_id = self.require_spot_visible(spot, current_user, "Spot is not visible to you")
        self.repos.shares.insert_one({"user_id": me_id, "spot_id": serialize_id(spot.get("_id")), "message": req.message, "created_at": datetime.now(UTC)})
        return {"ok": True}

    def create_support_ticket(self, req: SupportTicketRequest, current_user: dict[str, Any]) -> SupportTicketPublic:
        return self.support_actions.create_support_ticket(req, current_user)

    def list_all_support_tickets(self) -> list[SupportTicketPublic]:
        return self.support_actions.list_all_support_tickets()

    def update_ticket_status(self, ticket_id: str, ticket_status: str) -> SupportTicketPublic:
        return self.support_actions.update_ticket_status(ticket_id, ticket_status)

    def delete_ticket(self, ticket_id: str) -> dict[str, bool]:
        return self.support_actions.delete_ticket(ticket_id)

    def create_moderation_report(self, req: ModerationReportCreateRequest, current_user: dict[str, Any] | None) -> ModerationReportPublic:
        return self.moderation_actions.create_moderation_report(req, current_user)

    def list_moderation_notifications(self, current_user: dict[str, Any]) -> list[ModerationNotificationPublic]:
        return self.moderation_actions.list_moderation_notifications(current_user)

    def list_moderation_reports(self, report_status: str, limit: int) -> list[ModerationReportPublic]:
        return self.moderation_actions.list_moderation_reports(report_status, limit)

    def _set_target_content_status(self, target_type: str, target_id: str, moderation_status: str) -> None:
        normalized = as_text(target_type).lower()
        if normalized == "spot":
            target = self.spot_or_404(target_id)
            self.repos.spots.update_fields({"_id": target.get("_id")}, {"moderation_status": moderation_status})
            return
        if normalized == "comment":
            self.comment_or_404(target_id)
            self.repos.comments.update_fields({"_id": ObjectId(target_id)}, {"moderation_status": moderation_status, "updated_at": self._now()})
            return
        if normalized == "meetup":
            existing = self.meetup_or_404(target_id)
            self.repos.meetups.update_fields({"_id": existing.get("_id")}, {"moderation_status": moderation_status, "updated_at": self._now()})
            return
        if normalized == "meetup_comment":
            if not ObjectId.is_valid(target_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid comment ID")
            existing = self.repos.meetup_comments.find_one({"_id": ObjectId(target_id)})
            if not existing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
            self.repos.meetup_comments.update_fields({"_id": ObjectId(target_id)}, {"moderation_status": moderation_status, "updated_at": self._now()})

    def review_moderation_report(self, report_id: str, req: ModerationReportReviewRequest, admin_user: dict[str, Any]) -> ModerationReportPublic:
        return self.moderation_actions.review_moderation_report(report_id, req, admin_user)

    def list_moderated_users(self, query: str, limit: int) -> list[ModerationUserPublic]:
        return self.moderation_actions.list_moderated_users(query, limit)

    def update_user_moderation_status(self, user_id: str, req: ModerationUserStatusRequest, admin_user: dict[str, Any]) -> ModerationUserPublic:
        return self.moderation_actions.update_user_moderation_status(user_id, req, admin_user)

    def to_spot_comment(self, row: dict[str, Any] | None) -> SpotComment:
        return self.comment_actions.to_spot_comment(row)

    def list_comments(self, spot_id: str, current_user: dict[str, Any] | None) -> list[SpotComment]:
        return self.comment_actions.list_comments(spot_id, current_user)

    def create_comment(self, spot_id: str, req: CommentCreateRequest, current_user: dict[str, Any]) -> SpotComment:
        return self.comment_actions.create_comment(spot_id, req, current_user)

    def update_comment(self, comment_id: str, req: CommentUpdateRequest, current_user: dict[str, Any]) -> SpotComment:
        return self.comment_actions.update_comment(comment_id, req, current_user)

    def delete_comment(self, comment_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.comment_actions.delete_comment(comment_id, current_user)

    def sync_meetup_invites(self, meetup_id: str, host_user_id: str, invite_user_ids: list[str]) -> None:
        self.meetup_actions.sync_meetup_invites(meetup_id, host_user_id, invite_user_ids)

    def create_meetup(self, req: MeetupCreateRequest, current_user: dict[str, Any]) -> MeetupPublic:
        return self.meetup_actions.create_meetup(req, current_user)

    def list_meetups(self, scope: str, current_user: dict[str, Any]) -> list[MeetupPublic]:
        return self.meetup_actions.list_meetups(scope, current_user)

    def update_meetup(self, meetup_id: str, req: MeetupUpdateRequest, current_user: dict[str, Any]) -> MeetupPublic:
        return self.meetup_actions.update_meetup(meetup_id, req, current_user)

    def delete_meetup(self, meetup_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.meetup_actions.delete_meetup(meetup_id, current_user)

    def list_meetup_invites(self, current_user: dict[str, Any]) -> list[MeetupInviteRef]:
        return self.meetup_actions.list_meetup_invites(current_user)

    def respond_meetup(self, meetup_id: str, req: MeetupRespondRequest, current_user: dict[str, Any]) -> MeetupInviteRef:
        return self.meetup_actions.respond_meetup(meetup_id, req, current_user)

    def list_meetup_comments(self, meetup_id: str, current_user: dict[str, Any]) -> list[MeetupComment]:
        return self.meetup_actions.list_meetup_comments(meetup_id, current_user)

    def create_meetup_comment(self, meetup_id: str, req: MeetupCommentCreateRequest, current_user: dict[str, Any]) -> MeetupComment:
        return self.meetup_actions.create_meetup_comment(meetup_id, req, current_user)

    def update_meetup_comment(self, comment_id: str, req: MeetupCommentUpdateRequest, current_user: dict[str, Any]) -> MeetupComment:
        return self.meetup_actions.update_meetup_comment(comment_id, req, current_user)

    def delete_meetup_comment(self, comment_id: str, current_user: dict[str, Any]) -> dict[str, bool]:
        return self.meetup_actions.delete_meetup_comment(comment_id, current_user)

    def list_meetup_notifications(self, current_user: dict[str, Any]) -> list[MeetupNotificationPublic]:
        return self.meetup_actions.list_meetup_notifications(current_user)
