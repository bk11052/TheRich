import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from app.db import get_session
from app.models.lifelog import Photo
from app.schemas import PhotoRead

router = APIRouter(prefix="/photos", tags=["photos"])

# 업로드 저장 위치 (프로젝트 루트 기준). main.py 에서 /uploads 로 정적 서빙.
UPLOAD_DIR = Path("uploads")
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".svg"}
MAX_BYTES = 10 * 1024 * 1024  # 10MB


@router.post("", response_model=PhotoRead, status_code=201)
async def upload_photo(
    file: UploadFile = File(...),
    transaction_id: int | None = Form(default=None),
    session: Session = Depends(get_session),
) -> Photo:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"허용되지 않는 형식: {ext or '알수없음'}")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "파일이 너무 큽니다 (최대 10MB)")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / fname).write_bytes(data)

    obj = Photo(transaction_id=transaction_id, file_path=f"/uploads/{fname}")
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("", response_model=list[PhotoRead])
def list_photos(
    transaction_id: int | None = None, session: Session = Depends(get_session)
) -> list[Photo]:
    q = select(Photo)
    if transaction_id is not None:
        q = q.where(Photo.transaction_id == transaction_id)
    return list(session.exec(q.order_by(Photo.id)).all())


@router.delete("/{photo_id}", status_code=204)
def delete_photo(photo_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Photo, photo_id)
    if not obj:
        raise HTTPException(404, "photo not found")
    # 파일도 삭제 (실패해도 DB 레코드는 지움)
    try:
        fname = obj.file_path.rsplit("/", 1)[-1]
        (UPLOAD_DIR / fname).unlink(missing_ok=True)
    except OSError:
        pass
    session.delete(obj)
    session.commit()
