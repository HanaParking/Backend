from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Query
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
from app.models.parkingLot import ParkingSpotHistory  # 아래 3) 참고
from ultralytics import YOLO
import re
from typing import Dict, Any
from datetime import datetime, timezone
from app.crud import parkingLot as crud_parkingLot
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter()

UPLOAD_DIR = "upload_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # -> app/
AI_DIR = BASE_DIR / "ai"

ROI_JSON = AI_DIR / "roi_points.json"
MODEL_PATH = AI_DIR / "best_hana.pt"
CROP_SIZE = (200, 300)               # (width, height)
ROWS, COLS = 38, 28                  # 주차장 매트릭스 고정 크기

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
    (필요 시) ROI name에서 row/col을 파싱하는 보조 함수.
    이번 버전은 DB spot_id 매핑을 쓰므로 필수는 아님.
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

    # 3) 숫자-구분자-숫자
    m = re.fullmatch(r"(\d+)\s*[-_xX\s]\s*(\d+)", name)
    if m:
        return int(m.group(1)), int(m.group(2))

    # 4) 문자+숫자 (A1, AA12)
    m = re.fullmatch(r"([A-Za-z]+)\s*[-_ ]?\s*(\d+)", name)
    if m:
        row_letters = m.group(1)
        col_num = int(m.group(2))
        row_num = letters_to_num(row_letters)  # 문자=행(row)
        return row_num, col_num

    # 5) 숫자+문자 (12A, 7AA)
    m = re.fullmatch(r"(\d+)\s*[-_ ]?\s*([A-Za-z]+)", name)
    if m:
        row_num = int(m.group(1))
        col_letters = m.group(2)
        col_num = letters_to_num(col_letters)  # 문자=열(col)
        return row_num, col_num

    # 6) 백업: 문자열 내 숫자 2개
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

def blank_grids(rows: int = ROWS, cols: int = COLS):
    positions = [[0 for _ in range(cols)] for _ in range(rows)]     # 슬롯 존재 여부(0/1)
    car_exists = [[False for _ in range(cols)] for _ in range(rows)] # 점유 여부(True/False)
    return positions, car_exists

def get_spot_matrix_map(db: Session, lot_code: str) -> Tuple[Dict[str, Tuple[int, int]], List[Tuple[int, int]]]:
    """
    DB에서 lot_code의 모든 슬롯을 불러와
    spot_id -> (row_idx, col_idx) 매핑 생성 (0-based로 변환)
    또한 전체 좌표 리스트를 반환해 positions 생성에 사용.
    기대 스키마:
      row.spot_id: str
      row.spot_row: int (1-based)
      row.spot_column: int (1-based)
    """
    rows = crud_parkingLot.get_parking_spots_by_lot(db, lot_code)
    spot_map: Dict[str, Tuple[int, int]] = {}
    coords: List[Tuple[int, int]] = []

    for r in rows:
        i = int(r.spot_row) - 1  # 0-based
        j = int(r.spot_column) - 1
        if 0 <= i < ROWS and 0 <= j < COLS:
            sid = str(r.spot_id).strip()
            spot_map[sid] = (i, j)
            coords.append((i, j))
    return spot_map, coords

def build_positions_from_db(all_coords: List[Tuple[int, int]]) -> List[List[int]]:
    positions, _ = blank_grids()
    for (i, j) in all_coords:
        positions[i][j] = 1
    return positions

from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.models.parkingLot import ParkingSpotHistory

# infer + DB 저장
def infer_and_map(
    db: Session,
    lot_code: str,
    img_bgr: np.ndarray,
    ROI_DATA: List[dict],
    spot_map: Dict[str, Tuple[int, int]],
    positions: List[List[int]],
) -> List[List[int]]:

    ROWS = len(positions)
    COLS = len(positions[0]) if ROWS > 0 else 0

    car_exists = [[0 for _ in range(COLS)] for _ in range(ROWS)]

    dst_pts = np.float32([
        [0, 0],
        [CROP_SIZE[0], 0],
        [CROP_SIZE[0], CROP_SIZE[1]],
        [0, CROP_SIZE[1]],
    ])

    # ✅ Asia/Seoul 기준 '오늘' 날짜 (history_dt)
    today = datetime.now(ZoneInfo("Asia/Seoul")).date()

    # ✅ 배치 insert용 버퍼
    rows_to_insert = []

    for roi in ROI_DATA:
        spot_id = str(roi.get("name", "")).strip()  # 예: 'm252'
        pts = roi.get("points")

        if not spot_id or not pts or len(pts) != 4:
            continue
        if spot_id not in spot_map:
            continue

        (i, j) = spot_map[spot_id]
        if not (0 <= i < ROWS and 0 <= j < COLS and positions[i][j] == 1):
            continue

        try:
            src_pts = sort_points_clockwise(pts)
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(img_bgr, M, CROP_SIZE)

            # === YOLO 분류 ===
            result = MODEL(warped, verbose=False)
            label_idx = int(result[0].probs.top1)
            label_name = MODEL.names[label_idx]

            # empty면 0(차 없음), 그 외면 1(차 있음)
            occupied = 0 if label_name.lower() == "empty" else 1
            car_exists[i][j] = occupied

            # === ⬇️ 히스토리 INSERT 버퍼에 추가 (occupied_cd는 '0'/'1' 문자열) ===
            rows_to_insert.append({
                "history_dt": today,          # DATE
                # history_seq는 SERIAL → DB가 자동 채움
                "lot_code": lot_code,         # 예: 'A1'
                "spot_id": spot_id,           # 예: 'm252' (모델에서 String(10))
                "occupied_cd": "1" if occupied == 1 else "0",
                # created_at/updated_at은 server_default로 DB가 채움
            })

        except Exception:
            # 해당 ROI만 건너뛰고 계속
            pass

    # ✅ 한 번에 대량 INSERT (성능↑)
    if rows_to_insert:
        # 방법 1) 매핑 기반 벌크 인서트
        db.bulk_insert_mappings(ParkingSpotHistory, rows_to_insert)
        # 방법 2) 객체로 넣고 싶다면:
        # db.bulk_save_objects([ParkingSpotHistory(**row) for row in rows_to_insert])
        db.commit()

    return car_exists



# ---------- 엔드포인트 ----------
@router.post("/img_upload", response_model=UploadOut, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
):
    # ✅ lot_code 하드코딩
    lot_code = "A1"  # ← 여기에 원하는 주차장 코드 입력

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

    # 2) DB에서 slot_id -> (row,col) 매핑 및 전체 좌표 취득
    try:
        spot_map, all_coords = get_spot_matrix_map(db, lot_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 조회 실패: {e}")

    if not spot_map:
        raise HTTPException(status_code=404, detail=f"해당 주차장({lot_code}) 슬롯 정보가 없습니다.")

    # 3) DB 기준 positions(38x28, 슬롯=1) 구성
    positions = build_positions_from_db(all_coords)

    # 4) ROI 분류 결과를 해당 좌표에 반영 + DB 저장
    try:
        car_exists = infer_and_map(db, lot_code, img, ROI_DATA, spot_map, positions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추론 실패: {e}")

    # 5) Redis 저장 및 발행
    realtime_payload = {
        "positions": positions,          # 0/1 슬롯 존재 그리드
        "carExists": car_exists,         # 0/1 점유 여부
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    try:
        await redis.set("parking_detail_data", json.dumps(realtime_payload))
        await redis.publish("parking_detail_channel", "updated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis 발행 실패: {e}")

    # 6) 응답
    return {
        "filename": safe_name,
        "url": f"/upload_images/{safe_name}",
        "message": f"분석/발행 완료: lot={lot_code}, ROI={len(ROI_DATA)}, slots={len(all_coords)}"
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