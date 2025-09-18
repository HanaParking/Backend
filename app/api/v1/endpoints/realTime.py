from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from app.dependencies import get_redis

router = APIRouter()

@router.get("/ping")
async def redis_ping(r: Redis = Depends(get_redis)):
    pong = await r.ping()
    return {"redis": "ok" if pong else "fail"}
