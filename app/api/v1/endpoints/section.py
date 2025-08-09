# app/api/v1/section.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.dependencies import get_db
from app.models.section import SectionTest

router = APIRouter()

@router.get("/section_test")
def get_section_test(db: Session = Depends(get_db)):
    result = db.execute(select(SectionTest)).scalars().all()
    return [s.__dict__ for s in result]


