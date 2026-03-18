from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Sector, Station
from app.schemas.game import SectorPlayerView, SectorSnapshot


def get_sector_snapshot(db: Session, sector_id: str) -> SectorSnapshot:
    sector = db.scalar(
        select(Sector)
        .where(Sector.id == sector_id)
        .options(joinedload(Sector.stations).joinedload(Station.owner), joinedload(Sector.world_events))
    )
    if not sector:
        raise ValueError("Сектор не найден")
    return SectorSnapshot(
        sector_id=sector.id,
        sector_name=sector.name,
        market_mode=sector.market_mode,
        market_mood=sector.market_mood,
        players=[
            SectorPlayerView(
                station_id=station.id,
                station_name=station.name,
                owner_username=station.owner.username,
                specialization=station.specialization,
                level=station.level,
                reputation=station.reputation,
            )
            for station in sector.stations
        ],
        events=[
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "ends_at": event.ends_at.isoformat(),
            }
            for event in sorted(sector.world_events, key=lambda item: item.ends_at, reverse=True)[:8]
        ],
    )
