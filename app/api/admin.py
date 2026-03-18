from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission, require_role
from app.db.session import get_db
from app.models import AdminAuditLog, AdminRoleKey, BalanceParameter, ContentStatus, ContentType, User
from app.schemas.admin import (
    AdminAuditLogView,
    AdminAuthzView,
    AdminPlayerDetailView,
    AdminPlayerSummaryView,
    AdminPlayerUpdateRequest,
    AdminUserView,
    BalanceItemView,
    BalanceRevisionView,
    BalanceUpsertRequest,
    ContentDiffView,
    ContentItemView,
    ContentRevisionView,
    ContentUpsertRequest,
    RoleAssignmentRequest,
    ValidationResult,
)
from app.services.admin_definitions import get_effective_definitions, validate_content_payload
from app.services.admin_service import (
    assign_roles,
    content_diff,
    duplicate_content,
    effective_permissions,
    get_admin_player_detail,
    get_user_role_names,
    list_admin_users,
    list_audit_logs,
    list_balance,
    list_balance_revisions,
    list_content_items,
    list_content_revisions,
    list_admin_players,
    publish_balance,
    publish_content,
    rollback_balance,
    rollback_content,
    upsert_balance,
    upsert_content_draft,
    update_admin_player,
    wipe_player_progress,
    wipe_server_progress,
    get_content_item,
    change_content_status,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/authz/me", response_model=AdminAuthzView)
def admin_me(current_user: User = Depends(require_permission("admin.read")), db: Session = Depends(get_db)) -> AdminAuthzView:
    roles = get_user_role_names(db, current_user.id)
    return AdminAuthzView(
        user_id=current_user.id,
        username=current_user.username,
        roles=roles,
        permissions=effective_permissions(roles),
    )


@router.get("/users", response_model=list[AdminUserView])
def admin_users(current_user: User = Depends(require_permission("admin.read")), db: Session = Depends(get_db)) -> list[AdminUserView]:
    return list_admin_users(db)


@router.get("/players", response_model=list[AdminPlayerSummaryView])
def admin_players(
    current_user: User = Depends(require_permission("players.read")),
    db: Session = Depends(get_db),
) -> list[AdminPlayerSummaryView]:
    return list_admin_players(db)


@router.get("/players/{station_id}", response_model=AdminPlayerDetailView)
def admin_player_detail(
    station_id: str,
    current_user: User = Depends(require_permission("players.read")),
    db: Session = Depends(get_db),
) -> AdminPlayerDetailView:
    return get_admin_player_detail(db, station_id)


@router.patch("/players/{station_id}", response_model=AdminPlayerDetailView)
def admin_player_update(
    station_id: str,
    payload: AdminPlayerUpdateRequest,
    current_user: User = Depends(require_permission("players.edit")),
    db: Session = Depends(get_db),
) -> AdminPlayerDetailView:
    item = update_admin_player(db, current_user, station_id, payload)
    db.commit()
    return item


@router.post("/players/{station_id}/wipe", response_model=AdminPlayerDetailView)
def admin_player_wipe(
    station_id: str,
    current_user: User = Depends(require_permission("players.wipe")),
    db: Session = Depends(get_db),
) -> AdminPlayerDetailView:
    item = wipe_player_progress(db, current_user, station_id)
    db.commit()
    return item


@router.post("/server/wipe", response_model=dict[str, int])
def admin_server_wipe(
    current_user: User = Depends(require_permission("server.wipe")),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    result = wipe_server_progress(db, current_user)
    db.commit()
    return result


@router.post("/roles", response_model=dict[str, str])
def update_roles(
    payload: RoleAssignmentRequest,
    current_user: User = Depends(require_role(AdminRoleKey.super_admin)),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    assign_roles(db, current_user, payload)
    db.commit()
    return {"message": "Роли обновлены."}


@router.get("/audit", response_model=list[AdminAuditLogView])
def audit_log(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_permission("audit.read")),
    db: Session = Depends(get_db),
) -> list[AdminAuditLogView]:
    return [AdminAuditLogView.model_validate(item) for item in list_audit_logs(db, limit=limit)]


@router.get("/content", response_model=list[ContentItemView])
def content_list(
    content_type: ContentType | None = None,
    status: ContentStatus | None = None,
    search: str | None = None,
    current_user: User = Depends(require_permission("admin.read")),
    db: Session = Depends(get_db),
) -> list[ContentItemView]:
    return list_content_items(db, content_type=content_type, status=status, search=search)


@router.post("/content", response_model=ContentItemView)
def create_or_update_content(
    payload: ContentUpsertRequest,
    current_user: User = Depends(require_permission("content.edit")),
    db: Session = Depends(get_db),
) -> ContentItemView:
    item = upsert_content_draft(db, current_user, payload)
    db.commit()
    return item


@router.get("/content/{content_type}/{key}", response_model=ContentItemView)
def content_one(
    content_type: ContentType,
    key: str,
    current_user: User = Depends(require_permission("admin.read")),
    db: Session = Depends(get_db),
) -> ContentItemView:
    return get_content_item(db, content_type, key)


@router.patch("/content/{content_type}/{key}", response_model=ContentItemView)
def patch_content(
    content_type: ContentType,
    key: str,
    payload: ContentUpsertRequest,
    current_user: User = Depends(require_permission("content.edit")),
    db: Session = Depends(get_db),
) -> ContentItemView:
    if payload.content_type != content_type or payload.key != key:
        raise HTTPException(status_code=400, detail="Path and payload mismatch")
    item = upsert_content_draft(db, current_user, payload)
    db.commit()
    return item


@router.post("/content/{content_type}/{key}/publish", response_model=ContentItemView)
def content_publish(
    content_type: ContentType,
    key: str,
    current_user: User = Depends(require_permission("content.publish")),
    db: Session = Depends(get_db),
) -> ContentItemView:
    item = publish_content(db, current_user, content_type, key)
    db.commit()
    return item


@router.post("/content/{content_type}/{key}/duplicate", response_model=ContentItemView)
def content_duplicate(
    content_type: ContentType,
    key: str,
    new_key: str = Query(..., min_length=2),
    current_user: User = Depends(require_permission("content.edit")),
    db: Session = Depends(get_db),
) -> ContentItemView:
    item = duplicate_content(db, current_user, content_type, key, new_key)
    db.commit()
    return item


@router.post("/content/{content_type}/{key}/archive", response_model=ContentItemView)
def content_archive(
    content_type: ContentType,
    key: str,
    current_user: User = Depends(require_permission("content.publish")),
    db: Session = Depends(get_db),
) -> ContentItemView:
    item = change_content_status(db, current_user, content_type, key, ContentStatus.archived)
    db.commit()
    return item


@router.post("/content/{content_type}/{key}/disable", response_model=ContentItemView)
def content_disable(
    content_type: ContentType,
    key: str,
    current_user: User = Depends(require_permission("content.publish")),
    db: Session = Depends(get_db),
) -> ContentItemView:
    item = change_content_status(db, current_user, content_type, key, ContentStatus.disabled)
    db.commit()
    return item


@router.get("/content/{content_type}/{key}/revisions", response_model=list[ContentRevisionView])
def content_revisions(
    content_type: ContentType,
    key: str,
    current_user: User = Depends(require_permission("admin.read")),
    db: Session = Depends(get_db),
) -> list[ContentRevisionView]:
    return list_content_revisions(db, content_type, key)


@router.get("/content/{content_type}/{key}/diff", response_model=ContentDiffView)
def content_diff_view(
    content_type: ContentType,
    key: str,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    current_user: User = Depends(require_permission("admin.read")),
    db: Session = Depends(get_db),
) -> ContentDiffView:
    return content_diff(db, content_type, key, from_version, to_version)


@router.post("/content/{content_type}/{key}/rollback", response_model=ContentItemView)
def content_rollback(
    content_type: ContentType,
    key: str,
    version: int = Query(..., ge=1),
    current_user: User = Depends(require_permission("content.publish")),
    db: Session = Depends(get_db),
) -> ContentItemView:
    item = rollback_content(db, current_user, content_type, key, version)
    db.commit()
    return item


@router.get("/balance", response_model=list[BalanceItemView])
def balance_list(current_user: User = Depends(require_permission("admin.read")), db: Session = Depends(get_db)) -> list[BalanceItemView]:
    return list_balance(db)


@router.patch("/balance", response_model=BalanceItemView)
def balance_update(
    payload: BalanceUpsertRequest,
    current_user: User = Depends(require_permission("balance.edit")),
    db: Session = Depends(get_db),
) -> BalanceItemView:
    item = upsert_balance(db, current_user, payload)
    db.commit()
    return item


@router.post("/balance/{key}/publish", response_model=BalanceItemView)
def balance_publish(
    key: str,
    current_user: User = Depends(require_permission("balance.publish")),
    db: Session = Depends(get_db),
) -> BalanceItemView:
    item = publish_balance(db, current_user, key)
    db.commit()
    return item


@router.get("/balance/{key}/revisions", response_model=list[BalanceRevisionView])
def balance_revisions(
    key: str,
    current_user: User = Depends(require_permission("admin.read")),
    db: Session = Depends(get_db),
) -> list[BalanceRevisionView]:
    return list_balance_revisions(db, key)


@router.post("/balance/{key}/rollback", response_model=BalanceItemView)
def balance_rollback(
    key: str,
    version: int = Query(..., ge=1),
    current_user: User = Depends(require_permission("balance.publish")),
    db: Session = Depends(get_db),
) -> BalanceItemView:
    item = rollback_balance(db, current_user, key, version)
    db.commit()
    return item


@router.get("/definitions/effective", response_model=dict[str, object])
def effective_definitions(
    current_user: User = Depends(require_permission("admin.read")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return get_effective_definitions(db, force=True)


@router.post("/dev/validate-content", response_model=ValidationResult)
def validate_content(
    payload: ContentUpsertRequest,
    current_user: User = Depends(require_permission("content.edit")),
    db: Session = Depends(get_db),
) -> ValidationResult:
    return validate_content_payload(db, payload.content_type, payload.payload, current_key=payload.key)
