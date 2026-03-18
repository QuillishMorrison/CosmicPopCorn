import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.contracts import _serialize_contract
from app.db.session import SessionLocal, get_db
from app.models import ContractSource, DailyReport, User
from app.schemas.common import MessageResponse
from app.schemas.game import MarketStateView, ModuleActionRequest, PolicyRequest, ReportView, StationRenameRequest, StationView
from app.services.auth_service import get_user_from_access_token
from app.services.contract_service import list_contracts, npc_contract_visibility_limit, visible_npc_contracts_for_station
from app.services.market_service import get_market_state
from app.services.station_service import (
    apply_policy,
    build_or_upgrade_module,
    get_station_for_user,
    list_reports,
    rename_station,
    station_to_view,
)
from app.services.world_service import process_station_until

router = APIRouter(prefix="/station", tags=["station"])


def _live_snapshot(db: Session, user_id: str) -> dict[str, object]:
    station = get_station_for_user(db, user_id)
    process_station_until(db, station, datetime.now(UTC))
    db.commit()
    db.refresh(station)
    market = [
        MarketStateView.model_validate(item).model_dump(mode="json")
        for item in get_market_state(db, station.sector_id)
    ]
    npc_contracts = [
        _serialize_contract(contract)
        for contract in visible_npc_contracts_for_station(db, station)[:3]
    ]
    reports_payload = [report.model_dump(mode="json") for report in list_reports(db, station.id, limit=1)]
    return {
        "station": station_to_view(db, station).model_dump(mode="json"),
        "reports": reports_payload,
        "market": market,
        "npc_contracts": npc_contracts,
        "npc_contract_visibility": npc_contract_visibility_limit(station),
    }


@router.get("/me", response_model=StationView)
def get_my_station(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> StationView:
    station = get_station_for_user(db, current_user.id)
    process_station_until(db, station, datetime.now(UTC))
    db.commit()
    db.refresh(station)
    return station_to_view(db, station)


@router.post("/rename", response_model=StationView)
def rename(
    payload: StationRenameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StationView:
    station = get_station_for_user(db, current_user.id)
    rename_station(station, payload.name)
    db.commit()
    db.refresh(station)
    return station_to_view(db, station)


@router.get("/reports", response_model=list[ReportView])
def reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ReportView]:
    station = get_station_for_user(db, current_user.id)
    process_station_until(db, station, datetime.now(UTC))
    db.commit()
    db.refresh(station)
    return list_reports(db, station.id)


@router.websocket("/live")
async def live_station(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    with SessionLocal() as db:
        try:
            user = get_user_from_access_token(db, token)
        except HTTPException:
            await websocket.close(code=4401)
            return

    await websocket.accept()
    try:
        while True:
            with SessionLocal() as db:
                await websocket.send_json(_live_snapshot(db, user.id))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


@router.post("/claim-report", response_model=MessageResponse)
def claim_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> MessageResponse:
    station = get_station_for_user(db, current_user.id)
    pending = db.scalar(
        select(DailyReport)
        .where(DailyReport.station_id == station.id, DailyReport.claimed_at.is_(None))
        .order_by(DailyReport.ended_at.desc())
    )
    if not pending:
        raise HTTPException(status_code=404, detail="No pending report.")
    from datetime import UTC, datetime

    pending.claimed_at = datetime.now(UTC)
    db.commit()
    return MessageResponse(message="Отчёт подтверждён.")


@router.post("/upgrade-module", response_model=StationView)
def upgrade_module(
    payload: ModuleActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StationView:
    station = get_station_for_user(db, current_user.id)
    try:
        build_or_upgrade_module(db, station, payload.module_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(station)
    return station_to_view(db, station)


@router.post("/build-module", response_model=StationView)
def build_module(
    payload: ModuleActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StationView:
    return upgrade_module(payload, db, current_user)


@router.post("/set-policy", response_model=StationView)
def set_policy(
    payload: PolicyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StationView:
    station = get_station_for_user(db, current_user.id)
    apply_policy(station, payload.key, payload.value)
    db.commit()
    db.refresh(station)
    return station_to_view(db, station)


@router.post("/collect-rewards", response_model=StationView)
def collect_rewards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> StationView:
    from datetime import UTC, datetime

    station = get_station_for_user(db, current_user.id)
    process_station_until(db, station, datetime.now(UTC))
    db.commit()
    db.refresh(station)
    return station_to_view(db, station)
