from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import MessageResponse
from app.schemas.game import MetaPurchaseRequest, MetaUpgradeView
from app.services.meta_service import list_meta_upgrades, purchase_meta_upgrade
from app.services.station_service import get_station_for_user

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/tree", response_model=list[MetaUpgradeView])
def tree(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[MetaUpgradeView]:
    return [MetaUpgradeView.model_validate(item) for item in list_meta_upgrades(db, current_user.id)]


@router.post("/purchase", response_model=MessageResponse)
def purchase(
    payload: MetaPurchaseRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> MessageResponse:
    station = get_station_for_user(db, current_user.id)
    purchase_meta_upgrade(db, station, payload.key)
    db.commit()
    return MessageResponse(message="Улучшение куплено.")
