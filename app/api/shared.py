"""공유 예산(데이트비용) 현황 조회."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_member
from app.models.core import Member, Transaction
from app.services.period import month_range
from app.services.shared_budget import compute_status, get_shared_category

router = APIRouter(
    prefix="/shared",
    tags=["shared"],
    # owner 와 partner 모두 접근 가능한 유일한 영역.
    dependencies=[Depends(require_member)],
)


@router.get("/budget")
def shared_budget_status(
    month: str = Query(..., description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> dict:
    status = compute_status(session, month)
    if status is None:
        raise HTTPException(
            404, "공유 예산이 설정되지 않았습니다 (is_shared 카테고리 + 해당 월 예산 필요)"
        )
    return status


@router.get("/members")
def shared_members(session: Session = Depends(get_session)) -> list[dict]:
    """공유 화면에서 사람을 색으로 구분하기 위한 최소 정보.

    telegram_chat_id·role 은 의도적으로 빼고 내려준다 — partner 가 볼 이유가 없다.
    """
    rows = session.exec(
        select(Member).where(Member.active == True).order_by(Member.id)  # noqa: E712
    ).all()
    return [{"id": m.id, "name": m.name, "color": m.color} for m in rows]


@router.get("/transactions")
def shared_transactions(
    month: str = Query(..., description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> list[dict]:
    """공유 카테고리 거래만. 개인 지출은 어떤 경우에도 섞이지 않는다."""
    category = get_shared_category(session)
    if category is None:
        return []
    start, end = month_range(month)
    rows = session.exec(
        select(Transaction)
        .where(
            Transaction.category_id == category.id,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .order_by(Transaction.occurred_at.desc())
    ).all()
    return [
        {
            "id": t.id,
            "amount": t.amount,
            "occurred_at": t.occurred_at.isoformat(),
            "merchant": t.merchant,
            "payer_id": t.payer_id,
            "source": t.source.value,
        }
        for t in rows
    ]
