from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AdminRoleKey, User
from app.services.admin_service import effective_permissions, get_user_role_names
from app.services.auth_service import get_user_from_access_token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing access token.")
    token = authorization.split(" ", 1)[1]
    return get_user_from_access_token(db, token)


def require_permission(permission: str):
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        roles = get_user_role_names(db, current_user.id)
        permissions = effective_permissions(roles)
        if "*" in permissions or permission in permissions:
            return current_user
        raise HTTPException(status_code=403, detail="Недостаточно прав.")

    return dependency


def require_role(*allowed: AdminRoleKey):
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        roles = set(get_user_role_names(db, current_user.id))
        if roles.intersection(set(allowed)) or AdminRoleKey.super_admin in roles:
            return current_user
        raise HTTPException(status_code=403, detail="Недостаточно прав.")

    return dependency
