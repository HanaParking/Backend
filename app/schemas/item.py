from pydantic import BaseModel

# 아이템 DTO 정의
class ItemCreate(BaseModel):
    name: str

class ItemOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
