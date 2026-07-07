from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends, Query

from core.social.actions import SocialActions
from models.schemas import (
    CommentCreateRequest,
    CommentUpdateRequest,
    MeetupCommentCreateRequest,
    MeetupCommentUpdateRequest,
    MeetupCreateRequest,
    MeetupRespondRequest,
    MeetupUpdateRequest,
    ModerationReportCreateRequest,
    ModerationReportReviewRequest,
    ModerationUserStatusRequest,
    ShareRequest,
    SpotUpsertRequest,
    SupportTicketRequest,
    UpdateProfileRequest,
)


def _social_actions(repos):
    return SocialActions(repos)


def profile_read_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def read_me(current_user: dict = Depends(get_current_user)):
        return actions.get_me(current_user)

    return read_me


def profile_update_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def update_me(entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = UpdateProfileRequest.model_validate(entity_data)
        return actions.update_me(req, current_user)

    return update_me


def user_search_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def search_users(
        q: str = Query(default="", max_length=80),
        limit: int = Query(default=20, ge=1, le=50),
        current_user: dict = Depends(get_current_user),
    ):
        return actions.search_users(q, limit, current_user)

    return search_users


def user_profile_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_optional_current_user

    async def user_profile(user_id: str, current_user: dict | None = Depends(get_optional_current_user)):
        return actions.get_user_profile(user_id, current_user)

    return user_profile


def create_spot_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def create_spot(entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = SpotUpsertRequest.model_validate(entity_data)
        return actions.create_spot(req, current_user)

    return create_spot


def list_spots_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_optional_current_user

    async def list_spots(current_user: dict | None = Depends(get_optional_current_user)):
        return actions.list_visible_spots(current_user)

    return list_spots


def update_spot_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def update_spot(spot_id: str, entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = SpotUpsertRequest.model_validate(entity_data)
        return actions.update_spot(spot_id, req, current_user)

    return update_spot


def delete_spot_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def delete_spot(spot_id: str, current_user: dict = Depends(get_current_user)):
        return actions.delete_spot(spot_id, current_user)

    return delete_spot


def user_spots_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def user_spots(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.user_spots(user_id, current_user)

    return user_spots


def add_favorite_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def add_favorite(spot_id: str, current_user: dict = Depends(get_current_user)):
        return actions.add_favorite(spot_id, current_user)

    return add_favorite


def list_favorites_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def list_favorites(current_user: dict = Depends(get_current_user)):
        return actions.list_favorites(current_user)

    return list_favorites


def remove_favorite_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def remove_favorite(spot_id: str, current_user: dict = Depends(get_current_user)):
        return actions.remove_favorite(spot_id, current_user)

    return remove_favorite


def user_favorites_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def user_favorites(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.user_favorites(user_id, current_user)

    return user_favorites


def follow_user_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.follow_user(user_id, current_user)

    return follow_user


def unfollow_user_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def unfollow_user(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.unfollow_user(user_id, current_user)

    return unfollow_user


def follow_requests_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def follow_requests(current_user: dict = Depends(get_current_user)):
        return actions.follow_requests(current_user)

    return follow_requests


def approve_follow_request_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def approve_follow_request(follower_id: str, current_user: dict = Depends(get_current_user)):
        return actions.approve_follow_request(follower_id, current_user)

    return approve_follow_request


def reject_follow_request_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def reject_follow_request(follower_id: str, current_user: dict = Depends(get_current_user)):
        return actions.reject_follow_request(follower_id, current_user)

    return reject_follow_request


def followers_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def followers(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.followers(user_id, current_user)

    return followers


def following_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def following(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.following(user_id, current_user)

    return following


def remove_follower_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def remove_follower(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.remove_follower(user_id, current_user)

    return remove_follower


def block_user_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def block_user(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.block_user(user_id, current_user)

    return block_user


def unblock_user_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def unblock_user(user_id: str, current_user: dict = Depends(get_current_user)):
        return actions.unblock_user(user_id, current_user)

    return unblock_user


def blocked_users_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def blocked_users(current_user: dict = Depends(get_current_user)):
        return actions.blocked_users(current_user)

    return blocked_users


def share_spot_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def share_spot(spot_id: str, entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = ShareRequest.model_validate(entity_data)
        return actions.share_spot(spot_id, req, current_user)

    return share_spot


def create_support_ticket_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def create_support_ticket(entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = SupportTicketRequest.model_validate(entity_data)
        return actions.create_support_ticket(req, current_user)

    return create_support_ticket


def list_all_support_tickets_endpoint(repos):
    actions = _social_actions(repos)
    from core.admin_setup import get_current_admin_user

    async def list_all_support_tickets(_admin_user: dict = Depends(get_current_admin_user)):
        return actions.list_all_support_tickets()

    return list_all_support_tickets


def update_ticket_status_endpoint(repos):
    actions = _social_actions(repos)
    from core.admin_setup import get_current_admin_user

    async def update_ticket_status(
        ticket_id: str,
        ticket_status: str = Query(alias="status"),
        _admin_user: dict = Depends(get_current_admin_user),
    ):
        return actions.update_ticket_status(ticket_id, ticket_status)

    return update_ticket_status


def delete_ticket_endpoint(repos):
    actions = _social_actions(repos)
    from core.admin_setup import get_current_admin_user

    async def delete_ticket(ticket_id: str, _admin_user: dict = Depends(get_current_admin_user)):
        return actions.delete_ticket(ticket_id)

    return delete_ticket


def create_report_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_optional_current_user

    async def create_report(entity_data: Dict[str, Any], current_user: dict | None = Depends(get_optional_current_user)):
        req = ModerationReportCreateRequest.model_validate(entity_data)
        return actions.create_moderation_report(req, current_user)

    return create_report


def moderation_notifications_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def moderation_notifications(current_user: dict = Depends(get_current_user)):
        return actions.list_moderation_notifications(current_user)

    return moderation_notifications


def list_reports_endpoint(repos):
    actions = _social_actions(repos)
    from core.admin_setup import get_current_admin_user

    async def list_reports(
        status: str = Query(default="open", max_length=20),
        limit: int = Query(default=100, ge=1, le=300),
        _admin_user: dict = Depends(get_current_admin_user),
    ):
        return actions.list_moderation_reports(status, limit)

    return list_reports


def review_report_endpoint(repos):
    actions = _social_actions(repos)
    from core.admin_setup import get_current_admin_user

    async def review_report(
        report_id: str,
        req: ModerationReportReviewRequest,
        admin_user: dict = Depends(get_current_admin_user),
    ):
        return actions.review_moderation_report(report_id, req, admin_user)

    return review_report


def list_moderated_users_endpoint(repos):
    actions = _social_actions(repos)
    from core.admin_setup import get_current_admin_user

    async def list_users(
        q: str = Query(default="", max_length=80),
        limit: int = Query(default=100, ge=1, le=300),
        _admin_user: dict = Depends(get_current_admin_user),
    ):
        return actions.list_moderated_users(q, limit)

    return list_users


def update_user_status_endpoint(repos):
    actions = _social_actions(repos)
    from core.admin_setup import get_current_admin_user

    async def update_user_status(
        user_id: str,
        req: ModerationUserStatusRequest,
        admin_user: dict = Depends(get_current_admin_user),
    ):
        return actions.update_user_moderation_status(user_id, req, admin_user)

    return update_user_status


def create_comment_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def create_comment(spot_id: str, entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = CommentCreateRequest.model_validate(entity_data)
        return actions.create_comment(spot_id, req, current_user)

    return create_comment


def list_comments_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_optional_current_user

    async def list_comments(spot_id: str, current_user: dict | None = Depends(get_optional_current_user)):
        return actions.list_comments(spot_id, current_user)

    return list_comments


def update_comment_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def update_comment(comment_id: str, entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = CommentUpdateRequest.model_validate(entity_data)
        return actions.update_comment(comment_id, req, current_user)

    return update_comment


def delete_comment_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def delete_comment(comment_id: str, current_user: dict = Depends(get_current_user)):
        return actions.delete_comment(comment_id, current_user)

    return delete_comment


def create_meetup_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def create_meetup(entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = MeetupCreateRequest.model_validate(entity_data)
        return actions.create_meetup(req, current_user)

    return create_meetup


def list_meetups_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def list_meetups(scope: str = Query(default="upcoming"), current_user: dict = Depends(get_current_user)):
        return actions.list_meetups(scope, current_user)

    return list_meetups


def update_meetup_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def update_meetup(meetup_id: str, entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
        req = MeetupUpdateRequest.model_validate(entity_data)
        return actions.update_meetup(meetup_id, req, current_user)

    return update_meetup


def delete_meetup_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def delete_meetup(meetup_id: str, current_user: dict = Depends(get_current_user)):
        return actions.delete_meetup(meetup_id, current_user)

    return delete_meetup


def list_meetup_invites_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def list_meetup_invites(current_user: dict = Depends(get_current_user)):
        return actions.list_meetup_invites(current_user)

    return list_meetup_invites


def respond_meetup_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def respond_meetup(meetup_id: str, req: MeetupRespondRequest, current_user: dict = Depends(get_current_user)):
        return actions.respond_meetup(meetup_id, req, current_user)

    return respond_meetup


def list_meetup_comments_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def list_meetup_comments(meetup_id: str, current_user: dict = Depends(get_current_user)):
        return actions.list_meetup_comments(meetup_id, current_user)

    return list_meetup_comments


def create_meetup_comment_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def create_meetup_comment(meetup_id: str, req: MeetupCommentCreateRequest, current_user: dict = Depends(get_current_user)):
        return actions.create_meetup_comment(meetup_id, req, current_user)

    return create_meetup_comment


def update_meetup_comment_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def update_meetup_comment(comment_id: str, req: MeetupCommentUpdateRequest, current_user: dict = Depends(get_current_user)):
        return actions.update_meetup_comment(comment_id, req, current_user)

    return update_meetup_comment


def delete_meetup_comment_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def delete_meetup_comment(comment_id: str, current_user: dict = Depends(get_current_user)):
        return actions.delete_meetup_comment(comment_id, current_user)

    return delete_meetup_comment


def list_meetup_notifications_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def list_meetup_notifications(current_user: dict = Depends(get_current_user)):
        return actions.list_meetup_notifications(current_user)

    return list_meetup_notifications


def list_meetups_spots_endpoint(repos):
    actions = _social_actions(repos)
    from services.auth.current_user import get_current_user

    async def list_meetups_spots(current_user: dict = Depends(get_current_user)):
        return actions.list_visible_spots(current_user)

    return list_meetups_spots
