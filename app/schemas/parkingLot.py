from app.db.database import Base
from sqlalchemy import Column, Integer, String, Boolean

# 파이썬 클래스의 Todos를 DB todos 테이블과 매핑
class ParkingSpot(Base):
    # 이 클래스가 매핑 될 실제 DB의 테이블명
    __tablename__ = 'parking_spot_real'
    __table_args__ = {"schema": "hanaparking"}

    lot_code = Column(String(50), primary_key=True)
    spot_row = Column(Integer, primary_key=True)
    spot_column = Column(Integer, primary_key=True)
    occupied_cd = Column(String(1), nullable=False)
