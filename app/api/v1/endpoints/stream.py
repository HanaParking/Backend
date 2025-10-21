from typing import AsyncIterator
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import StreamingResponse
import redis.asyncio as redis
from app.core.redis_client import get_redis

router = APIRouter(prefix="/stream", tags=["stream"])

async def _sse(r: redis.Redis, channel: str) -> AsyncIterator[bytes]:
    pubsub = r.pubsub()
    try:
        await pubsub.subscribe(channel)
        async for msg in pubsub.listen():
            if msg and msg.get("type") == "message":
                data = msg.get("data")
                yield f"data: {data}\n\n".encode("utf-8")
    finally:
        try:
            await pubsub.unsubscribe(channel)
        finally:
            await pubsub.close()

@router.get("")
async def stream(lot_id: str = Query(...), request: Request = None, r: redis.Redis = Depends(get_redis)):
    channel = f"parking:{lot_id}"
    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(_sse(r, channel), media_type="text/event-stream", headers=headers)
