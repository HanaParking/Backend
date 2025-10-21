from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, TIMESTAMP, text
from app.db.database import Base

class ParkingLot(Base):
    __tablename__ = "parking_lot"
    __table_args__ = {"schema": "hanaparking"}  # 스키마 지정

    lot_code: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    lot_name: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    status_cd: Mapped[str] = mapped_column(String(1), nullable=False, server_default=text("'1'"))
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[str | None] = mapped_column(TIMESTAMP, nullable=True)
