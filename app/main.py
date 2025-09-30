from fastapi import FastAPI
from app.api.v1.routers import api_router
from app.db.database import engine, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="")

@app.get("/")
def read_root():
    return ("message : hello this is a library!")




