# app/api/v1/routers.py
from fastapi import APIRouter

# 기존 v1 엔드포인트들
from app.api.v1.endpoints import parkingLot
from app.api.v1.endpoints import files
from app.api.v1.endpoints import imgUpload

# 새로 만든 실시간/스냅샷 엔드포인트들 (app/endpoints/)
from app.api.v1.endpoints import parkingResult, parkingRead, stream

api_router = APIRouter()

# ===== 기존 =====
api_router.include_router(files.router,     prefix="/files",  tags=["files"])
api_router.include_router(imgUpload.router, prefix="/upload", tags=["Imgs"])
api_router.include_router(parkingLot.router, prefix="/lot",   tags=["lots"])

# ===== 새로 추가 (prefix는 각 파일 내부에서 이미 지정됨) =====
# parkingResult.py -> router = APIRouter(prefix="/parking", tags=["parking"])
api_router.include_router(parkingResult.router)  # => /api/v1/parking/result

# parkingRead.py -> router = APIRouter(prefix="/parking", tags=["parking"])
api_router.include_router(parkingRead.router)    # => /api/v1/parking/latest

# stream.py -> router = APIRouter(prefix="/stream", tags=["stream"])
api_router.include_router(stream.router)         # => /api/v1/stream
