from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import AdminRoleKey, MarketState, Role, Sector, User, UserRole
from app.schemas.auth import RegisterRequest
from app.services.admin_definitions import market_resource_definitions_map
from app.services.admin_service import ensure_roles_seeded, ensure_system_content_seeded
from app.services.auth_service import register_user
from app.services.meta_service import ensure_meta_catalog
from app.services.world_service import ensure_npc_contracts


def create_schema() -> None:
    Base.metadata.create_all(bind=engine)


def bootstrap_data(db: Session) -> None:
    ensure_roles_seeded(db)
    ensure_system_content_seeded(db)
    sector = db.scalar(select(Sector))
    if not sector:
        sector = Sector(name="Астер Вейл", market_mode="balanced", market_mood="Стабильные потоки, узкие спреды.")
        db.add(sector)
        db.flush()
    resource_map = market_resource_definitions_map(db)
    valid_market_resources = set(resource_map.keys())
    if valid_market_resources:
        db.query(MarketState).filter(
            MarketState.sector_id == sector.id,
            MarketState.resource.notin_(valid_market_resources),
        ).delete(synchronize_session=False)
    else:
        db.query(MarketState).filter(MarketState.sector_id == sector.id).delete(synchronize_session=False)

    existing_resources = {
        item.resource for item in db.scalars(select(MarketState).where(MarketState.sector_id == sector.id)).all()
    }
    for resource, definition in resource_map.items():
        if resource not in existing_resources:
            base_price = float(definition.get("base_price", 10))
            db.add(
                MarketState(
                    sector_id=sector.id,
                    resource=resource,
                    price=base_price,
                    trend=0.0,
                    history=[base_price],
                )
            )
    ensure_meta_catalog(db)
    ensure_npc_contracts(db, sector.id)
    settings = get_settings()
    if (
        settings.bootstrap_admin_email
        and settings.bootstrap_admin_username
        and settings.bootstrap_admin_password
        and not db.scalar(select(User).where(User.username == settings.bootstrap_admin_username.lower()))
    ):
        admin = register_user(
            db,
            RegisterRequest(
                email=settings.bootstrap_admin_email,
                username=settings.bootstrap_admin_username,
                password=settings.bootstrap_admin_password,
                station_name="Admin Relay",
                specialization="freight_hub",
            ),
        )
        role = db.scalar(select(Role).where(Role.key == AdminRoleKey.super_admin))
        if role:
            db.add(UserRole(user_id=admin.id, role_id=role.id))
    db.commit()
