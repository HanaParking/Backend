import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_USER = os.getenv("DATABASE_USER")

# 데이베이스 설정
DATABASE_URL = f"postgresql+psycopg2://{DATABASE_USER}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
