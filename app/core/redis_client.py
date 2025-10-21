import redis.asyncio as redis
from .settings import settings

_redis: redis.Redis | None = None

async def init_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,  # str로 다루기 편함
        )
        await _redis.ping()  # 연결 확인
    return _redis

async def get_redis() -> redis.Redis:
    # FastAPI Depends에서 사용
    return await init_redis()

async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
