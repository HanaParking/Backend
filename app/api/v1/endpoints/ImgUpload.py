from fastapi import APIRouter, File, UploadFile
from app.schemas.item import ItemOut
import os

# 아이템 관련 API 엔드포인트
router = APIRouter()

# 이미지를 저장할 디렉토리 설정
UPLOAD_DIR = "upload_images"
# UPLOAD_DIR 폴더가 없으면 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 아이템 생성
@router.post("/img_upload", response_model=ItemOut, status_code=201)
async def upload_image(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        return {"message": f"파일 '{file.filename}' 업로드 성공!"}
    except Exception as e:
        return {"message": f"파일 업로드 실패: {e}"}
