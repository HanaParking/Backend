from fastapi import APIRouter
from app.api.v1.endpoints import item
from app.api.v1.endpoints import section

# API 라우터 설정
api_router = APIRouter()

# 아이템 관련 API 엔드포인트 포함
api_router.include_router(item.router, prefix="/items", tags=["items"])

# API 엔드포인트 추가
api_router.include_router(section.router, prefix="/section")