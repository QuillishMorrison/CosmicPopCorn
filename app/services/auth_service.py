from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import RefreshToken, SecurityLog, Sector, User
from app.schemas.auth import AuthResponse, RegisterRequest
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, create_refresh_token, decode_token, hash_token
from app.services.admin_service import get_user_role_names
from app.services.station_service import create_station


settings = get_settings()
REFRESH_COOKIE_NAME = "sector_refresh_token"


def validate_password_strength(password: str) -> None:
    if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        raise HTTPException(status_code=400, detail="Пароль должен содержать буквы и цифры.")


def register_user(db: Session, payload: RegisterRequest) -> User:
    validate_password_strength(payload.password)
    existing = db.scalar(
        select(User).where(or_(User.email == payload.email.lower(), User.username == payload.username.lower()))
    )
    if existing:
        raise HTTPException(status_code=400, detail="Аккаунт уже существует.")
    sector = db.scalar(select(Sector))
    if not sector:
        sector = Sector(name="Aster Vale")
        db.add(sector)
        db.flush()
    user = User(
        email=payload.email.lower(),
        username=payload.username.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    create_station(db, user.id, sector.id, payload.station_name, payload.specialization)
    db.commit()
    db.refresh(user)
    return user


def issue_tokens(
    db: Session, user: User, response: Response, user_agent: str | None, ip_address: str | None
) -> AuthResponse:
    access_token, _ = create_access_token(user.id)
    raw_refresh = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )
    )
    db.add(
        SecurityLog(
            user_id=user.id,
            event_type="login_success",
            severity="info",
            ip_address=ip_address,
            detail={"user_agent": user_agent or ""},
        )
    )
    user.last_login_at = datetime.now(UTC)
    db.commit()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/auth",
    )
    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "roles": get_user_role_names(db, user.id),
        },
    )


def authenticate_user(db: Session, identity: str, password: str) -> User:
    user = db.scalar(select(User).where(or_(User.email == identity.lower(), User.username == identity.lower())))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учётные данные.")
    return user


def rotate_refresh_token(
    db: Session,
    raw_refresh_token: str | None,
    response: Response,
    user_agent: str | None,
    ip_address: str | None,
) -> AuthResponse:
    if not raw_refresh_token:
        raise HTTPException(status_code=401, detail="Отсутствует refresh token.")
    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(raw_refresh_token),
            RefreshToken.revoked_at.is_(None),
        )
    )
    if not token_record or token_record.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Refresh token истёк.")
    token_record.revoked_at = datetime.now(UTC)
    user = db.get(User, token_record.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Аккаунт недоступен.")
    return issue_tokens(db, user, response, user_agent, ip_address)


def logout_user(db: Session, raw_refresh_token: str | None, response: Response) -> None:
    if raw_refresh_token:
        token_record = db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh_token))
        )
        if token_record:
            token_record.revoked_at = datetime.now(UTC)
            db.commit()
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/auth")


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Текущий пароль неверный.")
    validate_password_strength(new_password)
    user.password_hash = hash_password(new_password)
    db.add(SecurityLog(user_id=user.id, event_type="password_changed", severity="info", detail={}))
    db.commit()


def get_user_from_access_token(db: Session, token: str) -> User:
    try:
        payload = decode_token(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Недействительный токен.") from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Недействительный токен.")
    user = db.get(User, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="Аккаунт не найден.")
    return user
