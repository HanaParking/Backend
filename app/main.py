# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# DB
from app.db.database import engine, Base
from app.api.v1.routers import api_router

# ✅ redis.asyncio 사용 (redis>=5)
import redis.asyncio as redis
from contextlib import asynccontextmanager

load_dotenv()

# Redis 서버 주소를 환경 변수에서 읽음
# 예: "redis://localhost:6379/0" → 로컬 Redis 0번 DB
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI의 lifespan 이벤트 핸들러로,
    앱이 시작될 때 Redis 연결을 생성하고
    종료될 때 Redis를 안전하게 닫는 역할을 함.
    """
    
    # --- Startup (앱 시작 시 실행) ---
    # Redis 연결 생성
    app.state.redis = redis.from_url(
        REDIS_URL,
        encoding="utf-8",          # 문자열 인코딩 설정
        decode_responses=True,     # 바이트 대신 문자열로 응답 받기
    )

    # Redis 서버에 ping 테스트
    try:
        pong = await app.state.redis.ping()  # Redis에 ping 요청 (연결 확인용)
        if pong is not True:
            # Redis가 pong 응답을 주지 않으면 오류 발생
            raise RuntimeError("Redis ping failed")
    except Exception as e:
        # 연결이 실패한 경우 예외를 발생시켜 앱 실행을 중단함
        raise RuntimeError(f"Redis connection failed: {e}")

    # yield 이후에 실제 애플리케이션이 실행됨
    yield  # <- 이 지점 이후에 FastAPI 라우터가 작동 시작

    # --- Shutdown (앱 종료 시 실행) ---
    # Redis 연결이 존재하면 닫음
    r: redis.Redis = getattr(app.state, "redis", None)
    if r:
        await r.close()
        app.state.redis = None  # 참조 제거로 메모리 정리

app = FastAPI(
    title="Hana Parking Project",
    description="API Documentation",
    version="1.0.0", 
    lifespan=lifespan
)

# ===== CORS =====
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://hanaparkingcop.com",
    "https://hanaparkingcop.com",
    "http://www.hanaparkingcop.com",
    "https://www.hanaparkingcop.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 운영에선 꼭 구체 도메인만!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== DB 테이블 생성 =====
Base.metadata.create_all(bind=engine)

# ===== 라우터 등록 =====
app.include_router(api_router, prefix="/api/v1")

# ===== Root =====
@app.get("/")
def read_root():
    return {"message": "hello this is hanaparking!"}

# ===== 정적 파일 =====
app.mount("/upload_images", StaticFiles(directory="upload_images"), name="upload_images")
