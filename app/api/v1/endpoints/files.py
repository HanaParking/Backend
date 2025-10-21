from fastapi import APIRouter
from typing import List
from pathlib import Path

router = APIRouter()

# 이미지 업로드 경로
UPLOAD_DIR = "upload_images"
BASE_DIR = Path(UPLOAD_DIR)

@router.get("/list")
def list_files():
    files = [x.name for x in BASE_DIR.iterdir()]
    return files
  
@router.delete("/delete")
def delete_files():
    deleted = []
    for x in BASE_DIR.iterdir():
        if x.is_file():
            x.unlink()
            deleted.append(x.name)
    return {"deleted":deleted}