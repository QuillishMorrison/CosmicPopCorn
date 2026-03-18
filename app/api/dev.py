from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.meta_service import ensure_meta_catalog
from app.services.world_service import maybe_spawn_event, world_tick
from app.tasks.seed import seed_database

settings = get_settings()
router = APIRouter(prefix="/admin/dev", tags=["dev"])


def _ensure_dev() -> None:
    if not settings.enable_dev_endpoints:
        raise HTTPException(status_code=404, detail="Unavailable.")


@router.post("/seed")
def seed(db: Session = Depends(get_db)) -> dict[str, str]:
    _ensure_dev()
    seed_database(db)
    ensure_meta_catalog(db)
    db.commit()
    return {"message": "Seeded."}


@router.post("/tick")
def tick(db: Session = Depends(get_db)) -> dict[str, int]:
    _ensure_dev()
    return world_tick(db)


@router.post("/event")
def event(db: Session = Depends(get_db)) -> dict[str, str]:
    _ensure_dev()
    maybe_spawn_event(db)
    db.commit()
    return {"message": "Event created."}
