from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import json

router = APIRouter(tags=["parking-fetch"])

def get_redis(request: Request):
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        raise RuntimeError("Redis client(app.state.redis)가 초기화되지 않았습니다.")
    return redis

@router.get("/parking/{lot_id}")
async def get_parking_status(lot_id: str, request: Request) -> Dict[str, Any]:
    """
    주차장 전체 상태 조회
    - lot:{lot_id} 해시에 저장된 모든 좌표의 상태를 가져옴
    """
    redis = get_redis(request)
    key = f"lot:{lot_id}"

    # HGETALL → dict[field] = value
    data: Dict[str, str] = await redis.hgetall(key)

    if not data:
        raise HTTPException(status_code=404, detail=f"{key}에 데이터가 없습니다.")

    # JSON 문자열을 파싱
    parsed: Dict[str, Any] = {}
    for coord, raw in data.items():
        try:
            parsed[coord] = json.loads(raw)
        except json.JSONDecodeError:
            parsed[coord] = {"raw": raw}  # 혹시 JSON이 아니면 원문 반환

    # 마지막 갱신 시각도 함께 가져오기
    updated_at = await redis.get(f"{key}:updated_at")

    return {
        "lot_id": lot_id,
        "updated_at": updated_at,
        "slots": parsed
    }

@router.get("/parking/{lot_id}/{coord}")
async def get_single_slot(lot_id: str, coord: str, request: Request) -> Dict[str, Any]:
    """
    특정 좌석(coord) 상태 조회
    """
    redis = get_redis(request)
    key = f"lot:{lot_id}"

    raw = await redis.hget(key, coord)
    if raw is None:
        raise HTTPException(status_code=404, detail=f"{key}에 {coord} 데이터가 없습니다.")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"raw": raw}

    return {
        "lot_id": lot_id,
        "coord": coord,
        "status": parsed
    }
