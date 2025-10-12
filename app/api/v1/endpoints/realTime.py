# app/api/v1/endpoints/realTime.py (예시)
from fastapi import APIRouter, Depends, HTTPException
from upstash_redis.asyncio import Redis as UpstashRedis
from app.dependencies import get_redis

router = APIRouter()

@router.get("/ping")
async def redis_ping(r: UpstashRedis = Depends(get_redis)):
    try:
        key = "healthcheck:ping"
        await r.set(key, "pong", ex=5)   # 5초 TTL 임시키
        got = await r.get(key)
        return {"redis": "ok" if got == "pong" else "fail"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}" )
