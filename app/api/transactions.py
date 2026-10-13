from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_owner
from app.models.core import Transaction
from app.models.lifelog import Tag, TransactionTag
from app.schemas import (
    TagRead,
    TransactionCreate,
    TransactionRead,
    TransactionTagsSet,
    TransactionUpdate,
)
from app.services.classify import classify
from app.services.lifelog import replace_tags, tags_of
from app.services.period import month_range

router = APIRouter(prefix="/transactions", tags=["transactions"], dependencies=[Depends(require_owner)])


@router.post("", response_model=TransactionRead, status_code=201)
def create_transaction(
    payload: TransactionCreate, session: Session = Depends(get_session)
) -> Transaction:
    data = payload.model_dump()
    # 카테고리 미지정이면 규칙엔진으로 자동 분류 시도
    if data.get("category_id") is None:
        data["category_id"] = classify(session, data.get("merchant"))
    obj = Transaction(**data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    month: str | None = Query(None, description="YYYY-MM"),
    account_id: int | None = None,
    category_id: int | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[Transaction]:
    q = select(Transaction)
    if account_id is not None:
        q = q.where(Transaction.account_id == account_id)
    if category_id is not None:
        q = q.where(Transaction.category_id == category_id)
    if month:
        start, end = month_range(month)
        q = q.where(Transaction.occurred_at >= start, Transaction.occurred_at < end)
    q = q.order_by(Transaction.occurred_at.desc()).offset(offset).limit(limit)
    return list(session.exec(q).all())


@router.get("/{txn_id}", response_model=TransactionRead)
def get_transaction(txn_id: int, session: Session = Depends(get_session)) -> Transaction:
    obj = session.get(Transaction, txn_id)
    if not obj:
        raise HTTPException(404, "transaction not found")
    return obj


@router.patch("/{txn_id}", response_model=TransactionRead)
def update_transaction(
    txn_id: int, payload: TransactionUpdate, session: Session = Depends(get_session)
) -> Transaction:
    obj = session.get(Transaction, txn_id)
    if not obj:
        raise HTTPException(404, "transaction not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{txn_id}", status_code=204)
def delete_transaction(txn_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Transaction, txn_id)
    if not obj:
        raise HTTPException(404, "transaction not found")
    session.delete(obj)
    session.commit()


@router.get("/{txn_id}/tags", response_model=list[TagRead])
def get_transaction_tags(
    txn_id: int, session: Session = Depends(get_session)
) -> list[Tag]:
    return tags_of(session, txn_id)


@router.put("/{txn_id}/tags", response_model=list[TagRead])
def set_transaction_tags(
    txn_id: int, payload: TransactionTagsSet, session: Session = Depends(get_session)
) -> list[Tag]:
    """거래의 태그를 payload.tag_ids 로 통째 교체."""
    if not session.get(Transaction, txn_id):
        raise HTTPException(404, "transaction not found")
    return replace_tags(session, txn_id, payload.tag_ids)
