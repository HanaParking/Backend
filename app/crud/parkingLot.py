from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.models.parkingLot import ParkingLot, ParkingSpotHistory, ParkingSpot

# 주차장(Lot)관련 CRUD 작업

# 구역별 주차자리 특성 테이블
def get_parkingLots(db: Session):
    return db.query(ParkingLot).all()

def get_RecentParkingSpot(db: Session):
    # 자리별(= lot_code + spot_id) 최신 1개: 날짜 최신 → 같은 날짜 내 시퀀스 최신
    rn = func.row_number().over(
        partition_by=(ParkingSpotHistory.lot_code, ParkingSpotHistory.spot_id),
        order_by=(desc(ParkingSpotHistory.history_dt),
                  desc(ParkingSpotHistory.history_seq))
    ).label("rn")

    subq = (
        db.query(
            ParkingSpotHistory.lot_code.label("lot_code"),
            ParkingSpotHistory.spot_id.label("spot_id"),
            ParkingSpotHistory.history_dt.label("history_dt"),
            ParkingSpotHistory.history_seq.label("history_seq"),
            rn
        )
        # 필요 시 특정 주차장만: .filter(ParkingSpotHistory.lot_code == 'A1')
        .subquery()
    )

    # 복합키로 원본과 조인 → ORM 객체 그대로 반환
    return (
        db.query(ParkingSpotHistory)
        .join(
            subq,
            and_(
                ParkingSpotHistory.lot_code == subq.c.lot_code,
                ParkingSpotHistory.spot_id == subq.c.spot_id,
                ParkingSpotHistory.history_dt == subq.c.history_dt,
                ParkingSpotHistory.history_seq == subq.c.history_seq,
            ),
        )
        .filter(subq.c.rn == 1)
        .all()
    )

def get_parking_spots_by_lot(db: Session, lot_code: str):
    """SELECT spot_id, spot_row, spot_column FROM hanaparking.parking_spot WHERE lot_code=:lot_code"""
    return (
        db.query(
            ParkingSpot.spot_id,
            ParkingSpot.spot_row,
            ParkingSpot.spot_column,
        )
        .filter(ParkingSpot.lot_code == lot_code)
        .order_by(ParkingSpot.spot_row.asc(), ParkingSpot.spot_column.asc(), ParkingSpot.spot_id.asc())
        .all()
    )