# DB Entity

from sqlalchemy import Column, Integer, String
from app.db.database import Base

class SectionTest(Base):
    __tablename__ = "section_test"

    parking_space = Column(String(50), primary_key=True, index=True)
    code = Column(String(1), unique=True, nullable=True)  # unique key
    tot_cnt = Column(Integer, nullable=False)

    