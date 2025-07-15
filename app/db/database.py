from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 데이베이스 설정
DATABASE_URL = "postgresql+psycopg2://postgres:db_pwd@localhost:50432/postgres"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
