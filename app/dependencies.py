from app.db.database import SessionLocal
from fastapi import Request, HTTPException
from upstash_redis.asyncio import Redis as UpstashRedis

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_redis(request: Request) -> UpstashRedis:
    r = getattr(request.app.state, "redis", None)
    if r is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    return r