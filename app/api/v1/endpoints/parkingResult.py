import json
from fastapi import APIRouter, Depends, HTTPException
import redis.asyncio as redis
from app.core.redis_client import get_redis
from app.schemas.parkingLot import ParkingSnapshot

router = APIRouter(prefix="/parking", tags=["parking"])

def _channel(lot_id: str) -> str:
    return f"parking:{lot_id}"

def _latest_key(lot_id: str) -> str:
    return f"parking:{lot_id}:latest"  # 최신 스냅샷 저장용

@router.post("/result")
async def publish_parking_result(snapshot: ParkingSnapshot, r: redis.Redis = Depends(get_redis)):
    """
    이미지 처리 후 나온 [1,0,1,...] 배열을 그대로 publish.
    - Redis Key에 최신 스냅샷 저장 + Pub/Sub으로 이벤트 발행
    """
    try:
        payload = snapshot.model_dump()
        data = json.dumps(payload, ensure_ascii=False, default=str)
        chan = _channel(snapshot.lot_id)
        key = _latest_key(snapshot.lot_id)

        # 원자적 실행: 최신값 저장(set) + publish
        async with r.pipeline(transaction=True) as pipe:
            await pipe.set(key, data)               # 최신 스냅샷 저장
            await pipe.publish(chan, data)          # 이벤트 발행
            res = await pipe.execute()

        receivers = res[-1]  # publish 리턴(구독자 수)
        return {"ok": True, "receivers": receivers, "channel": chan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
