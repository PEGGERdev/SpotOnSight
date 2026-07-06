from __future__ import annotations

import re
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status

from .ids import as_text, safe_user_projection, serialize_id
from .indexes import ensure_indexes
from .mappers import (
    to_moderation_notification_public,
    to_moderation_report_public,
    to_moderation_user_public,
)


class SocialModerationActions:
    def __init__(self, actions) -> None:
        self.actions = actions

    @property
    def repos(self):
        return self.actions.repos

    def create_moderation_report(self, req, current_user):
        ensure_indexes(self.repos)
        reporter_id = self.actions.me_id(current_user)
        target, target_owner_id = self.actions.moderation_support.target_content(req.target_type, req.target_id)
        normalized_target_type = as_text(req.target_type).lower()
        if normalized_target_type == "user" and target_owner_id == reporter_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot report yourself")
        if normalized_target_type != "user" and target_owner_id == reporter_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot report your own content")
        now = self.actions._now()
        doc = {
            "reporter_user_id": reporter_id,
            "target_type": normalized_target_type,
            "target_id": as_text(req.target_id),
            "target_owner_user_id": target_owner_id,
            "reason": as_text(req.reason) or "other",
            "details": as_text(req.details),
            "status": "open",
            "created_at": now,
        }
        inserted_id = self.repos.moderation_reports.insert_one(doc)
        row = self.repos.moderation_reports.find_one({"_id": ObjectId(inserted_id)})
        if not row:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Moderation report creation failed")
        return self.actions.moderation_support.moderation_report_public(row)

    def list_moderation_notifications(self, current_user):
        me_id = self.actions.me_id(current_user)
        rows = self.repos.moderation_notifications.find_many_sorted({"user_id": me_id}, sort_field="created_at", sort_direction=-1, limit=50)
        return [to_moderation_notification_public(row) for row in rows]

    def list_moderation_reports(self, report_status: str, limit: int):
        query = {}
        if report_status and report_status != "all":
            query["status"] = as_text(report_status).lower()
        rows = self.repos.moderation_reports.find_many_sorted(query, sort_field="created_at", sort_direction=-1, limit=limit)
        return [self.actions.moderation_support.moderation_report_public(row) for row in rows]

    def review_moderation_report(self, report_id: str, req, admin_user):
        ensure_indexes(self.repos)
        if not ObjectId.is_valid(report_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report ID")
        row = self.repos.moderation_reports.find_one({"_id": ObjectId(report_id)})
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        if as_text(row.get("status")).lower() != "open":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report already reviewed")

        action_taken = as_text(req.action).lower()
        severity = as_text(req.severity).lower()
        target_type = as_text(row.get("target_type")).lower()
        target_id = as_text(row.get("target_id"))
        target_owner_user_id = as_text(row.get("target_owner_user_id"))
        reviewed_by = self.actions.me_id(admin_user)
        admin_notes = as_text(req.admin_notes)
        timeout_until = None
        timeout_message = ""

        if req.status == "upheld":
            if action_taken == "hide_content" and target_type in {"spot", "comment", "meetup", "meetup_comment"}:
                self.actions._set_target_content_status(target_type, target_id, "hidden")
            if action_taken == "ban_user":
                if not ObjectId.is_valid(target_owner_user_id):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target owner could not be resolved")
                self.repos.users.update_fields(
                    {"_id": ObjectId(target_owner_user_id)},
                    {
                        "account_status": "banned",
                        "account_status_reason": admin_notes or f"Account banned after upheld moderation report: {as_text(row.get('reason'))}",
                        "posting_timeout_until": None,
                    },
                )
            if target_type in {"spot", "comment", "meetup", "meetup_comment"} and ObjectId.is_valid(target_owner_user_id):
                _weight, timeout_until, timeout_message = self.actions.moderation_support.apply_strike(
                    user_id=target_owner_user_id,
                    target_type=target_type,
                    target_id=target_id,
                    report_id=report_id,
                    reason=as_text(row.get("reason")),
                    severity=severity,
                    reviewed_by=reviewed_by,
                )
                self.actions.moderation_support.notify_user(
                    target_owner_user_id,
                    title="Content flagged",
                    message="One of your posts was flagged and a strike has been applied to your account.",
                    details=" ".join(
                        [
                            f"Reason: {as_text(row.get('reason')).replace('_', ' ')}.",
                            f"Severity: {severity}.",
                            "Continued violations can lead to posting restrictions or account bans.",
                            timeout_message if timeout_until and timeout_message else "",
                        ]
                    ).strip(),
                )

        updates = {
            "status": req.status,
            "severity": severity,
            "action_taken": action_taken,
            "admin_notes": admin_notes,
            "reviewed_at": self.actions._now(),
            "reviewed_by": reviewed_by,
        }
        self.repos.moderation_reports.update_fields({"_id": ObjectId(report_id)}, updates)
        updated = self.repos.moderation_reports.find_one({"_id": ObjectId(report_id)})
        if not updated:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Moderation report update failed")
        return self.actions.moderation_support.moderation_report_public(updated)

    def list_moderated_users(self, query: str, limit: int):
        regex = re.compile(re.escape(as_text(query)), re.IGNORECASE) if as_text(query) else None
        mongo_query: dict[str, Any] = {}
        if regex is not None:
            mongo_query = {"$or": [{"username": regex}, {"display_name": regex}, {"email": regex}]}
        rows = self.repos.users.find_many_sorted(mongo_query, sort_field="created_at", sort_direction=-1, projection=safe_user_projection(), limit=limit)
        out = []
        for row in rows:
            user_id = serialize_id(row.get("_id"))
            if not ObjectId.is_valid(user_id):
                continue
            active_weight, recent_count = self.actions.moderation_support.recent_strike_metrics(user_id)
            out.append(to_moderation_user_public(row, active_strike_weight=active_weight, recent_strike_count=recent_count))
        return out

    def update_user_moderation_status(self, user_id: str, req, admin_user):
        target_id, _target = self.actions.user_or_404(user_id)
        if target_id == self.actions.me_id(admin_user) and req.account_status == "banned":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot ban their own account")
        updates = {
            "account_status": req.account_status,
            "account_status_reason": as_text(req.reason),
            "posting_timeout_until": req.posting_timeout_until,
        }
        self.repos.users.update_fields({"_id": ObjectId(target_id)}, updates)
        updated = self.repos.users.find_one({"_id": ObjectId(target_id)}, safe_user_projection())
        if not updated:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User moderation update failed")
        message = "Your account moderation status has been updated by an administrator."
        if req.account_status == "banned":
            message = "Your account has been banned."
        elif req.posting_timeout_until:
            message = f"Your posting access is restricted until {req.posting_timeout_until.isoformat()}."
        self.actions.moderation_support.notify_user(target_id, title="Account update", message=message, details=as_text(req.reason))
        active_weight, recent_count = self.actions.moderation_support.recent_strike_metrics(target_id)
        return to_moderation_user_public(updated, active_strike_weight=active_weight, recent_strike_count=recent_count)
