from fastapi import APIRouter, Depends
from app.dependencies import get_db
from typing import Annotated
from sqlalchemy.orm import Session
from app.models.lot import lotOut
from app.schemas.lot import Lot

router = APIRouter()

# Todos 테이블에 있는 모든 값 조회(결과는 JSON 형식으로-schema에서 정의함)
@router.get("/parkingSpotList", response_model=list[lotOut])

# DB 세션 만드는 의존성 주입
def read_all(db: Annotated[Session, Depends(get_db)]):
    return db.query(Lot).all()