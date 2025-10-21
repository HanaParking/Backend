from sqlalchemy.orm import Session
from app.models.parkingLot import ParkingLot, ParkingSpotReal

# 주차장(Lot)관련 CRUD 작업

# 구역별 주차자리 특성 테이블
def get_parkingLots(db: Session):
    return db.query(ParkingLot).all()

# 실시간 주차자리 테이블
def get_ParkingSpotReal(db :Session):
    return db.query(ParkingSpotReal).all()