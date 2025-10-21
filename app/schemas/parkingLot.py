from pydantic import BaseModel, ConfigDict, Field, conint, model_validator
from typing import List, Literal, Optional
from datetime import datetime

Bit = conint(ge=0, le=1)  # 0 또는 1만 허용

class GetParkingLot(BaseModel):
    lot_code: str        # 주차장 코드
    lot_name: str        # 주차장 이름
    capacity: int       # 전체 주차 가능 수
    status_cd: str       # 상태 코드
    available: Optional[int] = 0      # 현재 이용 가능 수

    # ORM 객체에서 속성 읽어오기 허용
    model_config = ConfigDict(from_attributes=True)

# 실시간 자리 조회
class ParkingSpotRealOut(BaseModel):
    lot_code: str
    spot_row: int
    spot_column: int
    occupied_cd: str   

class ParkingSnapshot(BaseModel):
    lot_id: str = Field(..., description="주차장 ID (채널/키 네임에 사용)")
    slots: List[Bit] = Field(..., description="[1,0,1,...] 점유 배열 (index=슬롯ID)")
    version: int = Field(..., description="증분 버전(모델 inference 카운터 등)")
    ts: datetime = Field(default_factory=datetime.utcnow)
    kind: Literal["snapshot"] = "snapshot"
    # (선택) 길이 검증: 등록된 총 슬롯 수가 있다면 여기서 체크
    expected_len: Optional[int] = None

    @model_validator(mode="after")
    def _len_check(self):
        if self.expected_len is not None and len(self.slots) != self.expected_len:
            raise ValueError(f"slots length {len(self.slots)} != expected_len {self.expected_len}")
        return self