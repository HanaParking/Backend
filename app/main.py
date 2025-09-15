from fastapi import FastAPI
from app.db.database import engine
from app.db.database import Base
from app.api.v1.routers import api_router

app = FastAPI(
    title="Hana Parking Project",
    description="API Documentation",
    version="1.0.0"
)

#데이터베이스 엔진을 사용하여 모델 기반으로 테이블 생성
Base.metadata.create_all(bind=engine)
app.include_router(api_router, prefix="/api/v1")

# 실행 : uvicorn app.main:app --reload
@app.get("/")
def read_root():
    return ("message : hello this is hanaparking!")

