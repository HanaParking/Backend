from fastapi import APIRouter, Depends
from app.api.deps import get_db
from typing import Annotated
from sqlalchemy.orm import Session
from app.schemas.parkingLot import parkingSpotOut
from app.crud import parkingLot as crud_spot

router = APIRouter()

# 실시간 데이터 가져오기
@router.get("/realtimeSpot", response_model=list[parkingSpotOut])
def realtime_spot_list(db: Annotated[Session, Depends(get_db)]):
    return crud_spot.get_realtime_spot(db)