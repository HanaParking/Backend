import json
from fastapi import APIRouter, Depends, HTTPException, Query
import redis.asyncio as redis
from app.core.redis_client import get_redis

router = APIRouter(prefix="/parking", tags=["parking"])

def _latest_key(lot_id: str) -> str:
    return f"parking:{lot_id}:latest"

@router.get("/latest")
async def get_latest(lot_id: str = Query(...), r: redis.Redis = Depends(get_redis)):
    try:
        raw = await r.get(_latest_key(lot_id))
        if not raw:
            raise HTTPException(status_code=404, detail="No snapshot yet")
        return json.loads(raw)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
