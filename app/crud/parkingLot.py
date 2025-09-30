from sqlalchemy.orm import Session
from app.models.parkingLot import ParkingLot

# 주차장(Lot)관련 CRUD 작업

# 주차장 목록 조회
def get_parkingLots(db: Session)
    return db.query(ParkingLot).all()
