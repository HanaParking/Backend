from typing import List
from fastapi import Depends, APIRouter, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.parkingLot import GetParkingLot , ParkingSpotOut, ParkingSpotBasicOut
from app.crud import parkingLot as crud_parkingLot  # crud 모듈 임포트

router = APIRouter()

@router.get("/", response_model=List[GetParkingLot])
def get_parking_lots(db: Session = Depends(get_db)):
    # REDIS로 부터 실시간 자리수 데이터 조회
    
    # DB로 부터 주차장 기본 정보 조회
    parking_lots: List[GetParkingLot] = crud_parkingLot.get_parkingLots(db)
    return parking_lots

@router.get("/recent", response_model=List[ParkingSpotOut])
def get_parking_lots_real(db: Session = Depends(get_db)):
    # DB로 부터 실시간 주차장 정보 조회
    parking_lots_real: List[ParkingSpotOut] = crud_parkingLot.get_RecentParkingSpot(db)
    return parking_lots_real

# ★ 추가: 특정 Lot의 자리 좌표 조회
@router.get("/spots", response_model=List[ParkingSpotBasicOut])
def get_parking_spots(
    lot_code: str = Query(..., min_length=1, max_length=50, description="주차장 코드 (예: A1)"),
    db: Session = Depends(get_db),
):
    rows = crud_parkingLot.get_parking_spots_by_lot(db, lot_code)
    return rows