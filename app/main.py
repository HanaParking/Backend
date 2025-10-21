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

load_dotenv()

app = FastAPI(
    title="Hana Parking Project",
    description="API Documentation",
    version="1.0.0"
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

# ===== Redis Cloud 연결 =====
# - TLS(rediss) 지원
# - decode_responses=True 로 문자열 다루기 편하게
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

@app.on_event("startup")
async def on_startup():
    # Connection Pool 내부적으로 관리됨
    app.state.redis = redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        pong = await app.state.redis.ping()
        if pong is not True:
            raise RuntimeError("Redis ping failed")
    except Exception as e:
        # 실패 시 앱 띄우고 싶지 않으면 여기서 예외를 그대로 올려도 됨
        raise RuntimeError(f"Redis connection failed: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    r: redis.Redis = getattr(app.state, "redis", None)
    if r:
        await r.close()
        app.state.redis = None

# ===== 라우터 등록 =====
app.include_router(api_router, prefix="/api/v1")

# ===== 헬스체크(선택) =====
@app.get("/health/redis")
async def health_redis(request: Request):
    r: redis.Redis = request.app.state.redis
    try:
        await r.set("hp:health", "ok", ex=10)
        val = await r.get("hp:health")
        return {"redis": "ok", "echo": val}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {e}")

# ===== Root =====
@app.get("/")
def read_root():
    return {"message": "hello this is hanaparking!"}

# ===== 정적 파일 =====
app.mount("/upload_images", StaticFiles(directory="upload_images"), name="upload_images")
