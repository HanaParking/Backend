from fastapi import APIRouter
from app.api.v1.endpoints import item
from app.api.v1.endpoints import ImgUpload
from app.api.v1.endpoints import realTime
from app.api.v1.endpoints import diagnostics
from app.api.v1.endpoints import parkingResult
from app.api.v1.endpoints import parkingFetch
from app.api.v1.endpoints import lot

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

<<<<<<< HEAD
<<<<<<< HEAD
# 주차 결과 저장 및 조회 엔드포인트 추가
api_router.include_router(parkingResult.router) 
api_router.include_router(parkingFetch.router) 
=======
# 주차장(Lot) 관련 API 엔드포인트 포함
api_router.include_router(item.router, prefix="/parking-lots", tags=["parkingLots"])

>>>>>>> 44bdf1c (feat: 주차장 api 엔드포인트 및 스키마 추가)

=======
>>>>>>> 699392c (main : add for demo)
# API 엔드포인트 추가
api_router.include_router(lot.router, prefix="/lot", tags=["lots"])