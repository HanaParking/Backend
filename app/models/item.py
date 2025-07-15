from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.db.database import Base

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
