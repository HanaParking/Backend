from sqlalchemy.orm import Session
from app.models.item import Item
from app.schemas.item import ItemCreate

# 아이템 관련 CRUD 작업

# 아이템 조회
def get_item(db: Session, item_id: int):
    return db.query(Item).filter(Item.id == item_id).first()

# 아이템 목록 조회
def get_items(db: Session, skip: int = 0, limit: int = 10): # 페이지네이션 처리
    return db.query(Item).offset(skip).limit(limit).all()

# 아이템 생성
def create_item(db: Session, item: ItemCreate):
    db_item = Item(name=item.name)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item


def update_item(db: Session, item_id: int, new_name: str):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item:
        db_item.name = new_name
        db.commit()
        db.refresh(db_item)
    return db_item
