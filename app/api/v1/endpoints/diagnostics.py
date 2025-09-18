from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_redis
from upstash_redis.asyncio import Redis as UpstashRedis
import time, uuid

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

@router.get("/redis")
async def redis_diagnostics(r: UpstashRedis = Depends(get_redis)):
    if r is None:
        # lifespan에서 Redis 미설정 시
        raise HTTPException(status_code=503, detail="Redis not initialized")

    key = f"apicheck:{uuid.uuid4().hex}"
    want = "pong"
    t0 = time.perf_counter()
    await r.set(key, want, ex=10)  # 10초 TTL 임시키
    got = await r.get(key)
    dt_ms = round((time.perf_counter() - t0) * 1000, 2)

    ok = (got == want)
    return {
        "ok": ok,
        "roundtrip": {
            "key": key,
            "want": want,
            "got": got,
            "latency_ms": dt_ms,
            "ttl_sec": 10
        },
        "provider": "upstash",
        "notes": "Upstash REST round-trip set/get"
    }
