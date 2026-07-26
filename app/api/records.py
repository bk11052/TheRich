"""기록(라이프로그) = 사진·장소·태그로 보강된 거래 조회."""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models.core import Transaction
from app.models.lifelog import Photo, Place, Tag, TransactionTag
from app.schemas import PhotoRead, PlaceRead, RecordRead, TagRead
from app.services.period import month_range

router = APIRouter(prefix="/records", tags=["records"])


@router.get("", response_model=list[RecordRead])
def list_records(
    tag_id: int | None = None,
    month: str | None = Query(None, description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> list[RecordRead]:
    """사진/장소/태그 중 하나라도 있는 거래를 최신순으로."""
    # 보강된 거래 id 수집
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

    # 태그 필터: 해당 태그가 달린 거래만
    if tag_id is not None:
        tagged = set(
            session.exec(
                select(TransactionTag.transaction_id).where(
                    TransactionTag.tag_id == tag_id
                )
            ).all()
        )
        candidate_ids &= tagged

    if not candidate_ids:
        return []

    q = select(Transaction).where(Transaction.id.in_(candidate_ids))  # type: ignore[attr-defined]
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
        tag_rows = session.exec(
            select(Tag)
            .join(TransactionTag, TransactionTag.tag_id == Tag.id)  # type: ignore[arg-type]
            .where(TransactionTag.transaction_id == t.id)
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
                tags=[TagRead.model_validate(tg, from_attributes=True) for tg in tag_rows],
            )
        )
    return records
