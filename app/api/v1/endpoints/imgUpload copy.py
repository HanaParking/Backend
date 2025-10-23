from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os, uuid, re, json
import numpy as np
import cv2
from datetime import datetime, timezone
from typing import List, Tuple
from app.dependencies import get_db, get_redis
from app.schemas.imgUpload import UploadOut
from app.models.parkingLot import ParkingSpotHistory, ParkingSpotReal  # 아래 3) 참고
from ultralytics import YOLO
import re
from typing import Dict, Any

router = APIRouter()

# ---------- 전역 설정 ----------
UPLOAD_DIR = "upload_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # -> app/
AI_DIR = BASE_DIR / "ai"

ROI_JSON = AI_DIR / "roi_points.json"
MODEL_PATH = AI_DIR / "best_hana.pt"
CROP_SIZE = (200, 300)               # (width, height)

# ---------- 전역 로드 (1회) ----------
with open(ROI_JSON, "r") as f:
    ROI_DATA = json.load(f)  # [{name, points}, ...]

MODEL = YOLO(MODEL_PATH)

# ---------- 헬퍼 ----------
def sort_points_clockwise(pts):
    pts = np.array(pts)
    center = np.mean(pts, axis=0)
    pts = sorted(pts, key=lambda p: np.arctan2(p[1] - center[1], p[0] - center[0]))
    return np.array(pts, dtype=np.float32)



def letters_to_num(s: str) -> int:
    """
    'A'->1, 'B'->2, ... 'Z'->26, 'AA'->27, 'AB'->28 ... 엑셀 열 표기와 동일
    """
    s = s.upper()
    n = 0
    for ch in s:
        if not ('A' <= ch <= 'Z'):
            raise ValueError(f"Invalid letter in row/col: {ch}")
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n

def parse_row_col(roi: dict) -> Tuple[int, int]:
    """
    지원 패턴:
    1) 명시 키: {'spot_row':3,'spot_column':5} 또는 {'row':3,'col':5}
    2) R3C5 / r3c5
    3) 3-5, 3_5, 3x5, 3 5 등 숫자-구분자-숫자
    4) A1, AA12,  a-01  (문자+숫자)  -> 문자=행(row), 숫자=열(col)
    5) 12A, 7AA  (숫자+문자)        -> 숫자=행(row), 문자=열(col)
    """
    # 1) 명시 키
    if "spot_row" in roi and "spot_column" in roi:
        return int(roi["spot_row"]), int(roi["spot_column"])
    if "row" in roi and "col" in roi:
        return int(roi["row"]), int(roi["col"])

    name = str(roi.get("name", "")).strip()

    # 2) R3C5
    m = re.fullmatch(r"[Rr]\s*(\d+)\s*[Cc]\s*(\d+)", name)
    if m:
        return int(m.group(1)), int(m.group(2))

    # 3) 숫자-구분자-숫자 ( -, _, x, 공백 등 )
    m = re.fullmatch(r"(\d+)\s*[-_xX\s]\s*(\d+)", name)
    if m:
        return int(m.group(1)), int(m.group(2))

    # 4) 문자+숫자  (예: A1, AA12, a-01)
    m = re.fullmatch(r"([A-Za-z]+)\s*[-_ ]?\s*(\d+)", name)
    if m:
        row_letters = m.group(1)
        col_num = int(m.group(2))
        row_num = letters_to_num(row_letters)  # 문자=행(row)
        return row_num, col_num

    # 5) 숫자+문자  (예: 12A, 7AA)
    m = re.fullmatch(r"(\d+)\s*[-_ ]?\s*([A-Za-z]+)", name)
    if m:
        row_num = int(m.group(1))
        col_letters = m.group(2)
        col_num = letters_to_num(col_letters)  # 문자=열(col)
        return row_num, col_num

    # 6) 가장 마지막 안전장치: 문자열 내 숫자 2개 추출
    nums = re.findall(r"\d+", name)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])

    raise ValueError(f"ROI name에 row/col 파싱 실패: {name}")


def imdecode_upload(file_bytes: bytes) -> np.ndarray:
    """UploadFile 바이트를 OpenCV 이미지로."""
    file_array = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(file_array, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지 디코딩 실패")
    return img


@router.post("/img_upload", response_model=UploadOut, status_code=201)
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db), redis = Depends(get_redis),  ):
    # 1) 파일 저장 (정적 파일 제공용)
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        content = await file.read()
        img = imdecode_upload(content)  # 메모리에서 바로 OpenCV 이미지
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 업로드/디코딩 실패: {e}")

    # 2) YOLO 추론 + ROI 반복
    rows_to_insert: List[ParkingSpotHistory] = []
    today = datetime.now().date()  # Asia/Seoul 타임존까지 엄밀히 원하면 pytz로 변환

    try:
        for roi in ROI_DATA:
            src_pts = sort_points_clockwise(roi["points"])
            dst_pts = np.float32([
                [0, 0],
                [CROP_SIZE[0], 0],
                [CROP_SIZE[0], CROP_SIZE[1]],
                [0, CROP_SIZE[1]]
            ])

            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(img, M, CROP_SIZE)

            # YOLO 분류
            result = MODEL(warped, verbose=False)
            label_idx = int(result[0].probs.top1)
            label_name = MODEL.names[label_idx]
            # empty → 0, 그 외 → 1
            occupied_cd = '0' if label_name.lower() == "empty" else '1'

            spot_row, spot_col = parse_row_col(roi)
            lot_code = roi.get("lot_code") or roi.get("lotCode") or "A1"  # 필요시 고정/주입

            rows_to_insert.append(
                ParkingSpotHistory(
                    history_dt=today,
                    lot_code=lot_code,
                    spot_row=spot_row,
                    spot_column=spot_col,
                    occupied_cd=occupied_cd,
                    # created_at는 DB default CURRENT_TIMESTAMP 사용
                )
            )

            db.merge(
                ParkingSpotReal(
                lot_code=lot_code,
                spot_row=spot_row,
                spot_column=spot_col,
                occupied_cd=occupied_cd,
                )
            )

        # 3) DB INSERT (bulk)
        db.bulk_save_objects(rows_to_insert)
        db.commit()


        # ---------------------------
        # ✅ (추가) Redis에 업로드 + 발행
        # ---------------------------

        positions = [[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1],
]

        # 2) 크기 파악
        rows = len(positions)
        cols = len(positions[0]) if rows > 0 else 0

        # 3) 기본값 False로 채운 동일 크기 배열
        car_exists = [[False for _ in range(cols)] for _ in range(rows)]

        # 4) 모델 결과를 (row,col) -> bool(차 있음) 맵으로 준비
        #    occupied_cd: '0' = empty(차 없음), 그 외 = occupied(차 있음)
        occ_map = {}
        for r in rows_to_insert:
            rr = r.spot_row - 1  # 1-based → 0-based
            cc = r.spot_column - 1
            if 0 <= rr < rows and 0 <= cc < cols and positions[rr][cc] == 1:
                occ_map[(rr, cc)] = (r.occupied_cd != '0')

        # 5) positions에 따라 car_exists 채우기
        for i in range(rows):
            for j in range(cols):
                if positions[i][j] == 1:
                    # 분석 결과가 없으면 기본 False 유지
                    car_exists[i][j] = occ_map.get((i, j), False)
                # positions==0 인 곳은 기본 False 그대로

        # 6) Redis payload
        realtime_payload = {
            "positions": positions,
            "carExists": car_exists,  # 차가 있으면 True, 없으면 False
        }

        await redis.set("parking_detail_data", json.dumps(realtime_payload))
        await redis.publish("parking_detail_channel", "updated")
        # ---------------------------


    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"추론/DB 저장 실패: {e}")

    # 4) 응답
    return {
        "filename": safe_name,
        "url": f"/upload_images/{safe_name}",
        "message": f"분석 완료: {len(rows_to_insert)}개 스팟 저장",
    }

    
    # 최신 이미지 파일 경로 리턴
def _get_latest_image_path(upload_dir: str) -> Path | None:
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