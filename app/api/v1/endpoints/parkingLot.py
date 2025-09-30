from typing import List
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.parkingLot import ParkingLot, GetParkingLot
from app.crud import parkingLot as crud_parkingLot  # crud 모듈 임포트

router = APIRouter()

@router.get("/", response_model=List[GetParkingLot])
def get_parking_lots(db: Session = Depends(get_db)):
    # REDIS로 부터 실시간 자리수 데이터 조회
    
    # DB로 부터 주차장 기본 정보 조회
    parking_lots: List[ParkingLot] = crud_parkingLot.get_parkingLots(db)
    return parking_lots
