from fastapi import APIRouter
from app.api.v1.endpoints import item
from app.api.v1.endpoints import ImgUpload
from app.api.v1.endpoints import realTime
from app.api.v1.endpoints import diagnostics
from app.api.v1.endpoints import parkingLot
from app.api.v1.endpoints import RedisDetailPage

# API 라우터 설정
api_router = APIRouter()

# 아이템 관련 API 엔드포인트 포함
api_router.include_router(item.router, prefix="/items", tags=["items"])

# 라즈베리파이로부터 이미지 받는 엔드포인트
api_router.include_router(ImgUpload.router, prefix="/upload", tags=["Imgs"])

# 실시간 데이터 관련 API 엔드포인트 포함
api_router.include_router(realTime.router, prefix="/realtime", tags=["realtime"])

# Redis 진단 엔드포인트 추가
api_router.include_router(diagnostics.router) 

# 주차장(Lot) 관련 API 엔드포인트 포함
api_router.include_router(parkingLot.router, prefix="/parking-lots", tags=["parkingLots"])


# API 엔드포인트 추가
api_router.include_router(RedisDetailPage.router, prefix="/redis/detail", tags=["detail"]) 
