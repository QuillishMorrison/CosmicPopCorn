from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.game import SectorSnapshot
from app.services.sector_service import get_sector_snapshot
from app.services.station_service import get_station_for_user

router = APIRouter(prefix="/sector", tags=["sector"])


@router.get("/snapshot", response_model=SectorSnapshot)
def snapshot(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> SectorSnapshot:
    station = get_station_for_user(db, current_user.id)
    return get_sector_snapshot(db, station.sector_id)


@router.get("/players")
def players(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict[str, object]]:
    station = get_station_for_user(db, current_user.id)
    snapshot_data = get_sector_snapshot(db, station.sector_id)
    return [player.model_dump() for player in snapshot_data.players]


@router.get("/events")
def events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict[str, object]]:
    station = get_station_for_user(db, current_user.id)
    snapshot_data = get_sector_snapshot(db, station.sector_id)
    return snapshot_data.events


@router.get("/leaderboard-lite")
def leaderboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict[str, object]]:
    station = get_station_for_user(db, current_user.id)
    snapshot_data = get_sector_snapshot(db, station.sector_id)
    ranked = sorted(snapshot_data.players, key=lambda item: (item.level, item.reputation), reverse=True)
    return [player.model_dump() for player in ranked]
