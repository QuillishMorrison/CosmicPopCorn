from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import AuthResponse, ChangePasswordRequest, LoginRequest, RegisterRequest, UserPublic
from app.schemas.common import MessageResponse
from app.security.rate_limiter import ensure_auth_allowed, record_auth_attempt
from app.services.admin_service import get_user_role_names
from app.services.auth_service import (
    REFRESH_COOKIE_NAME,
    authenticate_user,
    change_password,
    issue_tokens,
    logout_user,
    register_user,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    identity = payload.email.lower()
    ip_address = _client_ip(request)
    ensure_auth_allowed(db, identity, ip_address, "register")
    user = register_user(db, payload)
    record_auth_attempt(db, identity, ip_address, "register", True)
    return issue_tokens(db, user, response, request.headers.get("user-agent"), ip_address)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    identity = payload.identity.lower()
    ip_address = _client_ip(request)
    ensure_auth_allowed(db, identity, ip_address, "login")
    try:
        user = authenticate_user(db, identity, payload.password)
        record_auth_attempt(db, identity, ip_address, "login", True)
        return issue_tokens(db, user, response, request.headers.get("user-agent"), ip_address)
    except Exception:
        record_auth_attempt(db, identity, ip_address, "login", False)
        raise


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    return rotate_refresh_token(db, raw_refresh_token, response, request.headers.get("user-agent"), _client_ip(request))


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> MessageResponse:
    logout_user(db, request.cookies.get(REFRESH_COOKIE_NAME), response)
    return MessageResponse(message="Вы вышли из аккаунта.")


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserPublic:
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        roles=get_user_role_names(db, current_user.id),
    )


@router.post("/change-password", response_model=MessageResponse)
def update_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    change_password(db, current_user, payload.current_password, payload.new_password)
    return MessageResponse(message="Пароль обновлён.")
