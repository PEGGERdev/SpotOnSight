from __future__ import annotations

from typing import Any

from bson import ObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from .token_service import token_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_auth_repository(request: Request):
    return request.app.state.auth_repository


def _find_user_by_id(repository, user_id: str) -> dict[str, Any] | None:
    text = str(user_id or "").strip()
    if not ObjectId.is_valid(text):
        return None
    return repository.find_one({"_id": ObjectId(text)})


def _lookup_user(request: Request, token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        payload = token_service.decode_access_token(token)
    except JWTError:
        return None

    user_id = str(payload.get("sub") or "").strip()
    if not user_id:
        return None

    user_doc = _find_user_by_id(get_auth_repository(request), user_id)
    if not user_doc:
        return None
    if str(user_doc.get("account_status") or "active").strip().lower() == "banned":
        return None
    return user_doc


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> dict[str, Any]:
    user = _lookup_user(request, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_current_user(
    request: Request,
    token: str | None = Depends(optional_oauth2_scheme),
) -> dict[str, Any] | None:
    return _lookup_user(request, token)
