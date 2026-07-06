from __future__ import annotations

import os
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import Depends, HTTPException, status

from services.auth.current_user import get_current_user
from models.schemas import AuthUserRecord
from services.auth.password_service import password_service


ADMIN_DEFAULT_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip().lower()
ADMIN_DEFAULT_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123!")
ADMIN_DEFAULT_EMAIL = os.getenv("ADMIN_EMAIL", "admin@spotonsight.app").strip().lower()
ADMIN_DEFAULT_DISPLAY = os.getenv("ADMIN_DISPLAY", "System Administrator").strip()


def _is_admin_user(user_doc: dict) -> bool:
    return bool(user_doc.get("is_admin", False))


def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not _is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def ensure_admin_user(repository) -> dict | None:
    existing = repository.find_one({"username": ADMIN_DEFAULT_USERNAME})

    if existing:
        if not _is_admin_user(existing):
            repository.update_fields({"_id": existing["_id"]}, {"is_admin": True})
            existing["is_admin"] = True
        return existing

    admin_user = AuthUserRecord(
        username=ADMIN_DEFAULT_USERNAME,
        email=ADMIN_DEFAULT_EMAIL,
        password_hash=password_service.hash_password(ADMIN_DEFAULT_PASSWORD),
        display_name=ADMIN_DEFAULT_DISPLAY,
        bio="System Administrator - Full access to all features",
        is_admin=True,
        created_at=datetime.now(UTC),
    )

    doc = admin_user.model_dump()
    doc["_id"] = ObjectId()

    try:
        repository.insert_one(doc)
        return repository.find_one({"username": ADMIN_DEFAULT_USERNAME})
    except Exception:
        return None


def is_admin_user(user_doc: dict | None) -> bool:
    if user_doc is None:
        return False
    return _is_admin_user(user_doc)
