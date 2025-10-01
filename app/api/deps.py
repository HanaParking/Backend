from app.db.database import SessionLocal

def get_db():
    # 세션 인스턴스 만들기
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
