from fastapi import APIRouter
from app.api.v1.endpoints import parkingLot

api_router = APIRouter()

api_router.include_router(parkingLot.router, prefix="/parking", tags=["parkinglot"])