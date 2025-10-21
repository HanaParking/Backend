from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, TIMESTAMP, DateTime, Date, text, func
from app.db.database import Base
from typing import Optional

# 구역별 주차장 자리 특성 테이블
class ParkingLot(Base):
    __tablename__ = "parking_lot"
    __table_args__ = {"schema": "hanaparking"}  # 스키마 지정

    lot_code: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    lot_name: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    status_cd: Mapped[str] = mapped_column(String(1), nullable=False, server_default=text("'1'"))
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[str | None] = mapped_column(TIMESTAMP, nullable=True)

# 주차장 자리 이력 테이블
class ParkingSpotHistory(Base):
    __tablename__ = "parking_spot_history"
    __table_args__ = {"schema": "hanaparking"}  # 스키마 지정

    # PK: (history_dt, history_seq)
    history_dt: Mapped[str] = mapped_column(Date, primary_key=True, nullable=False)
    history_seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    lot_code: Mapped[str] = mapped_column(String(50), nullable=False)
    spot_row: Mapped[int] = mapped_column(Integer, nullable=False)
    spot_column: Mapped[int] = mapped_column(Integer, nullable=False)
    occupied_cd: Mapped[str] = mapped_column(String(1), nullable=False)
    created_at: Mapped[Optional[str]] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[Optional[str]] = mapped_column(DateTime, nullable=True)

# 실시간 주차장 자리 테이블
class ParkingSpotReal(Base):
    __tablename__ = "parking_spot_real"
    __table_args__ = {"schema": "hanaparking"}  # 스키마 지정

    # PK: (lot_code, spot_row, spot_column)
    lot_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    spot_row: Mapped[int] = mapped_column(Integer, primary_key=True)
    spot_column: Mapped[int] = mapped_column(Integer, primary_key=True)
    occupied_cd: Mapped[str] = mapped_column(String(1), nullable=False)