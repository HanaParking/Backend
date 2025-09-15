from pydantic import BaseModel, ConfigDict

# 아이템 DTO 정의
class ItemCreate(BaseModel):
    name: str

class ItemOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

#이미지 업로드 응답 모델
class UploadOut(BaseModel):
    filename: str
    url: str | None = None
    message: str
    model_config = ConfigDict(from_attributes=True)