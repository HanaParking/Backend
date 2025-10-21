from pydantic import BaseModel

class GetParkingLot(BaseModel):
    lotCode: str        # 주차장 코드
    lotName: str        # 주차장 이름
    capacity: int       # 전체 주차 가능 수
    statusCd: str       # 상태 코드
    available: int      # 현재 이용 가능 수
