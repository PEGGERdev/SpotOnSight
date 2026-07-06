from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from core.text import normalize_email, normalize_search_text, normalize_username
from services.auth.password_service import password_service

from .ids import as_text, normalize_social_accounts, safe_user_projection, serialize_id, viewer_user_id
from .indexes import ensure_indexes
from .mappers import to_user_public
from .policies import is_blocked_pair


class SocialProfileActions:
    def __init__(self, actions) -> None:
        self.actions = actions

    @property
    def repos(self):
        return self.actions.repos

    def get_me(self, current_user: dict[str, Any]):
        return to_user_public(current_user)

    def update_me(self, req, current_user: dict[str, Any]):
        ensure_indexes(self.repos)
        updates: dict[str, Any] = {}
        if req.username is not None:
            username = normalize_username(req.username)
            updates["username"] = username
            updates["username_key"] = normalize_search_text(username)
            updates["username_search"] = normalize_search_text(username)
        if req.email is not None:
            email = normalize_email(req.email)
            updates["email"] = email
            updates["email_key"] = normalize_email(email)
        if req.display_name is not None:
            updates["display_name"] = as_text(req.display_name)
            updates["display_name_search"] = normalize_search_text(req.display_name)
        if req.bio is not None:
            updates["bio"] = as_text(req.bio)
        if req.avatar_image is not None:
            updates["avatar_image"] = as_text(req.avatar_image)
        if req.social_accounts is not None:
            updates["social_accounts"] = normalize_social_accounts(req.social_accounts)
        if req.follow_requires_approval is not None:
            updates["follow_requires_approval"] = bool(req.follow_requires_approval)
        if req.new_password is not None:
            current_password = as_text(req.current_password)
            if not current_password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is required")
            current_hash = as_text(current_user.get("password_hash"))
            if not password_service.verify_password(current_password, current_hash):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
            updates["password_hash"] = password_service.hash_password(req.new_password)
        if not updates:
            return to_user_public(current_user)
        try:
            self.repos.users.update_fields({"_id": current_user["_id"]}, updates)
        except DuplicateKeyError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists") from exc
        updated = self.repos.users.find_one({"_id": current_user["_id"]})
        if not updated:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile update failed")
        return to_user_public(updated)

    def search_users(self, query: str, limit: int, current_user: dict[str, Any]):
        text = normalize_search_text(query)
        if not text:
            return []
        me_id = viewer_user_id(current_user)
        regex = re.compile(re.escape(text), re.IGNORECASE)
        users = self.repos.users.find_many(
            {
                "$or": [
                    {"username_search": regex},
                    {"display_name_search": regex},
                    {"username": regex},
                    {"display_name": regex},
                ]
            },
            safe_user_projection(),
            limit=limit,
        )
        out = []
        for user_doc in users:
            user_id = serialize_id(user_doc.get("_id"))
            if user_id == me_id or is_blocked_pair(self.repos, me_id, user_id):
                continue
            out.append(to_user_public(user_doc))
        return out

    def get_user_profile(self, user_id: str, current_user: dict[str, Any] | None):
        target_id, target = self.actions.user_or_404(user_id)
        me_id = viewer_user_id(current_user)
        if not self.actions.is_admin(current_user) and me_id != target_id and is_blocked_pair(self.repos, me_id, target_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        active_weight = 0
        recent_count = 0
        if self.actions.is_admin(current_user):
            active_weight, recent_count = self.actions.moderation_support.recent_strike_metrics(target_id)
        return to_user_public(target, active_strike_weight=active_weight, recent_strike_count=recent_count)
