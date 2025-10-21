from fastapi import APIRouter, File, UploadFile
from app.schemas.item import UploadOut
from pathlib import Path
from fastapi.responses import HTMLResponse
import os
import uuid
from typing import Optional

# 아이템 관련 API 엔드포인트
router = APIRouter()

# 이미지를 저장할 디렉토리 설정
UPLOAD_DIR = "upload_images"
# UPLOAD_DIR 폴더가 없으면 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 아이템 생성
@router.post("/img_upload", response_model=UploadOut, status_code=201)
async def upload_image(file: UploadFile = File(...)):
    try:
        safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        return {
            "filename": safe_name,
            "url": f"/upload_images/{safe_name}",  # main.py에서 StaticFiles mount 필요
            "message": f"파일 '{file.filename}' 업로드 성공!",
        }
    except Exception as e:
        return {"filename": "", "url": None, "message": f"파일 업로드 실패: {e}"}
    
    # 최신 이미지 파일 경로 리턴
def _get_latest_image_path(upload_dir: str) -> Optional[Path] :
    p = Path(upload_dir)
    if not p.exists():
        return None
    files = [f for f in p.iterdir() if f.is_file()]
    if not files:
        return None
    # 수정시간 최신순
    latest = max(files, key=lambda f: f.stat().st_mtime)
    return latest

@router.get("/img_latest", response_class=HTMLResponse, tags=["Imgs"])
def view_latest_image():
    latest = _get_latest_image_path(UPLOAD_DIR)

    if latest is None:
        body = """
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Latest Image</title>
            <style>
                html,body{height:100%;margin:0}
                body{display:flex;align-items:center;justify-content:center;background:#0b0b0d;color:#eee;font-family:system-ui,Segoe UI,Roboto,Apple Color Emoji,Noto Color Emoji,sans-serif}
                .card{max-width:90vw;text-align:center;opacity:.9}
                .msg{font-size:18px}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="msg">업로드된 이미지가 아직 없습니다.</div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=body, status_code=200)

    # 업로드 폴더는 main.py에서 /upload_images 로 mount 할 예정
    img_url = f"/upload_images/{latest.name}"

    body = f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Latest Image</title>
        <style>
            html,body{{height:100%;margin:0}}
            body{{display:flex;align-items:center;justify-content:center;background:#0b0b0d;color:#eee;font-family:system-ui,Segoe UI,Roboto,Apple Color Emoji,Noto Color Emoji,sans-serif}}
            .wrap{{display:flex;flex-direction:column;align-items:center;gap:12px}}
            img{{max-width:90vw;max-height:90vh;object-fit:contain;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.5)}}
            .name{{opacity:.8;font-size:14px}}
            .bar{{position:fixed;top:10px;left:50%;transform:translateX(-50%);opacity:.75;font-size:12px}}
            button{{background:#1f6feb;color:#fff;border:none;padding:6px 10px;border-radius:8px;cursor:pointer}}
            button:hover{{filter:brightness(1.1)}}
        </style>
    </head>
    <body>
        <div class="bar">
            <button onclick="location.reload()">새로고침</button>
        </div>
        <div class="wrap">
            <img src="{img_url}" alt="{latest.name}" />
            <div class="name">{latest.name}</div>
        </div>
        <!-- 자동 새로고침 원하면 아래 주석 해제 (5초마다) -->
        <!-- <script>setInterval(()=>location.reload(), 5000);</script> -->
    </body>
    </html>
    """
    return HTMLResponse(content=body, status_code=200)