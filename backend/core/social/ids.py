from __future__ import annotations

from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status

from core.text import normalize_login as normalize_login_text, normalize_text

from .repositories import SocialRepositories


def serialize_id(value: Any) -> str:
    if isinstance(value, ObjectId):
        return str(value)
    return str(value or "")


def as_text(value: Any) -> str:
    return normalize_text(value)


def as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def normalize_login(value: Any) -> str:
    return normalize_login_text(value)


def normalize_social_accounts(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, item in value.items():
        k = as_text(key)
        v = as_text(item)
        if not k or not v or len(k) > 40 or len(v) > 500:
            continue
        out[k] = v
    return out


def normalize_id_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in value:
        sid = as_text(raw)
        if not ObjectId.is_valid(sid) or sid in seen:
            continue
        seen.add(sid)
        out.append(sid)
    return out


def spot_owner_id(spot_doc: dict[str, Any]) -> str:
    return as_text(spot_doc.get("owner_id"))


def spot_visibility(spot_doc: dict[str, Any]) -> str:
    visibility = as_text(spot_doc.get("visibility") or "public").lower()
    if visibility in {"public", "following", "invite_only", "personal"}:
        return visibility
    return "public"


def safe_user_projection() -> dict[str, int]:
    return {
        "username": 1,
        "email": 1,
        "display_name": 1,
        "bio": 1,
        "avatar_image": 1,
        "social_accounts": 1,
        "follow_requires_approval": 1,
        "is_admin": 1,
        "account_status": 1,
        "account_status_reason": 1,
        "posting_timeout_until": 1,
        "created_at": 1,
    }


def parse_object_id(value: str) -> ObjectId:
    text = as_text(value)
    if not ObjectId.is_valid(text):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    return ObjectId(text)


def spot_lookup_query(spot_id: str) -> dict[str, Any]:
    text = as_text(spot_id)
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    if ObjectId.is_valid(text):
        oid = ObjectId(text)
        return {"$or": [{"_id": oid}, {"_id": text}]}
    return {"_id": text}


def spot_document_by_id(r: SocialRepositories, spot_id: str) -> dict[str, Any] | None:
    return r.spots.find_one(spot_lookup_query(spot_id))


def viewer_user_id(current_user: dict[str, Any] | None) -> str:
    if current_user is None:
        return ""
    return serialize_id(current_user.get("_id"))
