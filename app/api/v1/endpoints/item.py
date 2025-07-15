from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.item import ItemCreate, ItemOut
from app.crud import item as crud_item
from app.dependencies import get_db
from typing import List

# 아이템 관련 API 엔드포인트
router = APIRouter()

# 아이템 생성
@router.post("/", response_model=ItemOut, status_code=201)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    return crud_item.create_item(db, item)

# 아이템 조회
@router.get("/{item_id}", response_model=ItemOut)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud_item.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

# 아이템 목록 조회
@router.get("/", response_model=List[ItemOut])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud_item.get_items(db, skip=skip, limit=limit)
