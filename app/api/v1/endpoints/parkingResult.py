from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
import json

router = APIRouter(tags=["parking-result"])

# ======== Pydantic Models ========
class SlotResult(BaseModel):
    coord: str = Field(..., description="주차 자리 좌표(필드명)")
    status: Any = Field(..., description="자리 상태 (예: 1/0, 'occupied'/'empty', True/False 등)")

    @validator("coord")
    def _coord_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("coord는 비어있을 수 없습니다.")
        return v

class SaveResultRequest(BaseModel):
    lot_id: str = Field(..., description="주차장 코드")
    results: List[SlotResult] = Field(..., min_items=1, description="모델 결과 목록")
    expire_seconds: Optional[int] = Field(0, ge=0, description="키 만료(초). 0이면 미설정")

# ======== Utils ========
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _normalize_status(val: Any) -> Any:
    """
    상태값 정규화:
    - True/'true'/'occupied'/'1' -> 1
    - False/'false'/'empty'/'0' -> 0
    - 그 외는 문자열/숫자 그대로 저장
    """
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ("1", "true", "occupied", "yes", "on"):
            return 1
        if s in ("0", "false", "empty", "no", "off"):
            return 0
        return val  # 기타 문자열은 그대로
    return val

def get_redis(request: Request):
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        raise RuntimeError("Redis client(app.state.redis)가 초기화되지 않았습니다.")
    return redis
# --- 호환 헬퍼 ---
async def hset_compat(redis, key: str, mapping: Dict[str, str]) -> None:
    """
    Upstash(HTTP)과 redis-py(redis.asyncio) 모두에서 동작하도록 hset 호출을 호환 처리.
    1) redis-py: hset(key, mapping=...)
    2) Upstash:  hset(key, fields=...)
    3) 그래도 안되면 개별 필드로 반복 저장
    """
    try:
        # redis.asyncio (redis-py)
        await redis.hset(key, mapping=mapping)
        return
    except TypeError:
        pass
    try:
        # Upstash (HTTP SDK)
        await redis.hset(key, fields=mapping)
        return
    except TypeError:
        pass

    # 최후의 보루: 개별 필드로 저장 (어떤 클라이언트든 100% 동작)
    for f, v in mapping.items():
        await redis.hset(key, f, v)

# ======== Endpoint ========
@router.post("/parking/result")
async def save_parking_result(req: SaveResultRequest, request: Request):
    redis = get_redis(request)
    key = f"lot:{req.lot_id}"
    now_iso = _utc_now_iso()

    # 1) HSET에 넣을 맵핑 만들기 (value는 반드시 문자열)
    mapping: Dict[str, str] = {}
    for item in req.results:
        value_obj = {
            "status": _normalize_status(item.status),
            "timestamp": now_iso,
        }
        mapping[item.coord] = json.dumps(value_obj, ensure_ascii=False)

    if not mapping:
        raise HTTPException(status_code=400, detail="results가 비어 있습니다.")

    # 2) Upstash: dict는 fields= 로 전달 (redis.asyncio는 mapping=)
    #    Upstash를 쓰는 경우:
    await hset_compat(redis, key, mapping)
    #    만약 redis.asyncio(TCP) 클라이언트라면 아래처럼 바꾸세요:
    # await redis.hset(key, mapping=mapping)

    # 3) 만료(키 전체 TTL)
    if req.expire_seconds and req.expire_seconds > 0:
        await redis.expire(key, req.expire_seconds)

    # 4) 마지막 갱신시각 저장 (ex는 양수일 때만)
    if req.expire_seconds and req.expire_seconds > 0:
        await redis.set(f"{key}:updated_at", now_iso, ex=req.expire_seconds)
    else:
        await redis.set(f"{key}:updated_at", now_iso)

    return {
        "ok": True,
        "key": key,
        "updated_fields": list(mapping.keys()),
        "timestamp": now_iso,
        "expire_seconds": req.expire_seconds or 0,
    }
