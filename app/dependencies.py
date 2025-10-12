from app.db.database import SessionLocal
from fastapi import Request, HTTPException
# from upstash_redis.asyncio import Redis as UpstashRedis
from redis import asyncio as aioredis  # pub/sub구조 이용을 위해서는 redis버전 4.2 이상 사용. 현재 사용버전은 6.4.0

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_redis(request: Request) -> aioredis.Redis:
    """
    FastAPI 앱 상태에서 Redis 인스턴스를 가져오는 의존성 함수.
    SSE(pub/sub)나 캐시 조회 시 사용됩니다.
    """
    r = getattr(request.app.state, "redis", None)
    if r is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    return r

# async def get_redis(request: Request) -> UpstashRedis:
#     r = getattr(request.app.state, "redis", None)
#     if r is None:
#         raise HTTPException(status_code=503, detail="Redis not initialized")
#     return r