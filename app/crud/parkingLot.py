from sqlalchemy.orm import Session
from app.models.parkingLot import ParkingSpot

def get_realtime_spot(db: Session):
    return db.query(ParkingSpot).all()