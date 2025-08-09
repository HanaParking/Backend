from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 데이베이스 설정
# postgresql 서버 연결해서 샤용해야함. 여기에 적으면 해킹우려로 추후 서버에 해당 값 적재해서 불러오도록 변경 필요
DATABASE_URL = "postgresql+psycopg2://postgres:db_pwd@localhost:50432/postgres"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()