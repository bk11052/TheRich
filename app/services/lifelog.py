"""기록(라이프로그) 도메인 로직: 사진·장소·태그로 보강된 거래.

owner 용 라우터(/records, /photos, /places, /tags, /transactions/{id}/tags)와
partner 용 라우터(/shared/*)가 같은 로직을 쓰도록 여기로 모았다.
권한(누가 어떤 거래를 건드릴 수 있나)은 라우터가 판단하고, 이 모듈은 판단하지 않는다.
"""

import uuid
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.models.core import Transaction
from app.models.lifelog import Photo, Place, Tag, TransactionTag
from app.schemas import PhotoRead, PlaceRead, RecordRead, TagRead
from app.services import geocode
from app.services.period import month_range

# 업로드 저장 위치 (프로젝트 루트 기준, settings.upload_dir). main.py 에서 /uploads 로 정적 서빙.
UPLOAD_DIR = Path(settings.upload_dir)
MAX_PHOTO_BYTES = 10 * 1024 * 1024  # 10MB

# SVG 는 스크립트를 품을 수 있고, /uploads 는 API 와 같은 출처에서 서빙된다.
# 그래서 남이 올린 파일은 래스터 이미지만 받는다(owner 본인 업로드만 SVG 허용).
RASTER_EXT = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic"})
OWNER_EXT = RASTER_EXT | {".svg"}


class PhotoRejected(ValueError):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def save_photo(
    session: Session,
    *,
    filename: str | None,
    data: bytes,
    transaction_id: int | None,
    allowed_ext: frozenset[str] | set[str],
) -> Photo:
    ext = Path(filename or "").suffix.lower()
    if ext not in allowed_ext:
        raise PhotoRejected(400, f"허용되지 않는 형식: {ext or '알수없음'}")
    if len(data) > MAX_PHOTO_BYTES:
        raise PhotoRejected(413, "파일이 너무 큽니다 (최대 10MB)")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / fname).write_bytes(data)

    obj = Photo(transaction_id=transaction_id, file_path=f"/uploads/{fname}")
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def tags_of(session: Session, txn_id: int) -> list[Tag]:
    return list(
        session.exec(
            select(Tag)
            .join(TransactionTag, TransactionTag.tag_id == Tag.id)  # type: ignore[arg-type]
            .where(TransactionTag.transaction_id == txn_id)
        ).all()
    )


def replace_tags(session: Session, txn_id: int, tag_ids: list[int]) -> list[Tag]:
    """거래의 태그를 tag_ids 로 통째 교체. 존재하지 않는 태그 id 는 무시한다."""
    for link in session.exec(
        select(TransactionTag).where(TransactionTag.transaction_id == txn_id)
    ).all():
        session.delete(link)
    for tag_id in dict.fromkeys(tag_ids):  # 중복 제거, 순서 유지
        if session.get(Tag, tag_id):
            session.add(TransactionTag(transaction_id=txn_id, tag_id=tag_id))
    session.commit()
    return tags_of(session, txn_id)


def create_place(session: Session, data: dict) -> Place:
    """장소 생성. 좌표가 없고 카카오 키가 있으면 상호명으로 자동 지오코딩."""
    if data.get("lat") is None and data.get("lng") is None:
        hit = geocode.geocode_place(data["name"])
        if hit:
            for field in ("address", "region", "lat", "lng", "kakao_place_id"):
                if data.get(field) is None and hit.get(field) is not None:
                    data[field] = hit[field]
    obj = Place(**data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def list_records(
    session: Session,
    *,
    tag_id: int | None = None,
    month: str | None = None,
    category_id: int | None = None,
) -> list[RecordRead]:
    """사진/장소/태그 중 하나라도 있는 거래를 최신순으로.

    category_id 를 주면 그 카테고리 거래만 — partner 에게 공유 카테고리만 보여줄 때 쓴다.
    """
    photo_tx = set(
        session.exec(
            select(Photo.transaction_id).where(Photo.transaction_id.is_not(None))  # type: ignore[union-attr]
        ).all()
    )
    tag_tx = set(session.exec(select(TransactionTag.transaction_id)).all())
    placed_tx = set(
        session.exec(select(Transaction.id).where(Transaction.place_id.is_not(None))).all()  # type: ignore[union-attr]
    )
    candidate_ids = photo_tx | tag_tx | placed_tx

    if tag_id is not None:
        tagged = set(
            session.exec(
                select(TransactionTag.transaction_id).where(TransactionTag.tag_id == tag_id)
            ).all()
        )
        candidate_ids &= tagged

    if not candidate_ids:
        return []

    q = select(Transaction).where(Transaction.id.in_(candidate_ids))  # type: ignore[attr-defined]
    if category_id is not None:
        q = q.where(Transaction.category_id == category_id)
    if month:
        start, end = month_range(month)
        q = q.where(Transaction.occurred_at >= start, Transaction.occurred_at < end)
    txns = list(session.exec(q.order_by(Transaction.occurred_at.desc())).all())

    records: list[RecordRead] = []
    for t in txns:
        place = session.get(Place, t.place_id) if t.place_id else None
        photos = session.exec(
            select(Photo).where(Photo.transaction_id == t.id).order_by(Photo.id)
        ).all()
        records.append(
            RecordRead(
                id=t.id,
                type=t.type,
                amount=t.amount,
                occurred_at=t.occurred_at,
                merchant=t.merchant,
                memo=t.memo,
                category_id=t.category_id,
                place=PlaceRead.model_validate(place, from_attributes=True) if place else None,
                photos=[PhotoRead.model_validate(p, from_attributes=True) for p in photos],
                tags=[TagRead.model_validate(tg, from_attributes=True) for tg in tags_of(session, t.id)],
            )
        )
    return records
