from pydantic import BaseModel, ConfigDict

#이미지 업로드 응답 모델
class UploadOut(BaseModel):
    filename: str
    url: str | None = None
    message: str
    model_config = ConfigDict(from_attributes=True)
