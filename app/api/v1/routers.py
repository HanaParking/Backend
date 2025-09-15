from fastapi import APIRouter
from app.api.v1.endpoints import item
from app.api.v1.endpoints import ImgUpload

# API 라우터 설정
api_router = APIRouter()

# 아이템 관련 API 엔드포인트 포함
api_router.include_router(item.router, prefix="/items", tags=["items"])

# 라즈베리파이로부터 이미지 받는 엔드포인트
api_router.include_router(ImgUpload.router, prefix="/upload", tags=["Imgs"])


# API 엔드포인트 추가
