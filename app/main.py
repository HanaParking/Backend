from fastapi import FastAPI
from app.db.database import engine
from app.db.database import Base
from app.api.v1.routers import api_router
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from upstash_redis.asyncio import Redis as UpstashRedis
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()  # .env -> os.environ

    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        raise RuntimeError("UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN 환경변수를 설정하세요.")

    # Upstash 클라이언트 생성 (HTTP 기반, 커넥션 풀/close 필요 없음)
    app.state.redis = UpstashRedis(url=url, token=token)

    # (선택) 헬스체크 — Upstash SDK에 ping이 없을 수 있어 간단 set/get으로 확인
    try:
        await app.state.redis.set("healthcheck", "ok", ex=10)
        _ = await app.state.redis.get("healthcheck")
    except Exception as e:
        # 필요하면 로그로만 남기고 계속 진행 가능
        raise RuntimeError(f"Upstash Redis 연결 실패: {e}") from e

    try:
        yield
    finally:
        # Upstash는 HTTP 호출이라 별도 close 불필요
        # (그래도 인터페이스가 있을 경우를 대비해 try/except)
        try:
            close = getattr(app.state.redis, "close", None)
            if callable(close):
                await close()
        except Exception:
            pass


app = FastAPI(
    title="Hana Parking Project",
    description="API Documentation",
    version="1.0.0",
    lifespan=lifespan, 
)

#데이터베이스 엔진을 사용하여 모델 기반으로 테이블 생성
Base.metadata.create_all(bind=engine)
app.include_router(api_router, prefix="/api/v1")

# 실행 : uvicorn app.main:app --reload
@app.get("/")
def read_root():
    return ("message : hello this is hanaparking!")

app.mount("/upload_images", StaticFiles(directory="upload_images"), name="upload_images")
