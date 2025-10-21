import os
from pydantic import BaseModel

class Settings(BaseModel):
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # Redis Cloud면 rediss://

settings = Settings()
