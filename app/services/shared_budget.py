"""공유 예산(데이트비용) 집계.

`Category.is_shared=True` 인 카테고리의 해당 월 Budget 이 공유 한도가 되고,
그 카테고리로 분류된 지출 합이 소진액이 된다. 정산(1/N)은 하지 않고
'누가 얼마 냈는지' 기여 내역만 보여준다.
"""

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.base import TxnType
from app.models.core import Budget, Category, Member, Transaction
from app.services.period import month_range

# 이 비율을 넘어서는 순간 경고. 넘은 뒤에는 매번 알리지 않고 상태만 'over' 로 둔다.
WARN_RATIO = 0.8


def get_shared_category(session: Session) -> Category | None:
    """공유 카테고리. 여러 개면 가장 먼저 만든 것(id 순)을 쓴다."""
    return session.exec(
        select(Category).where(Category.is_shared == True).order_by(Category.id)  # noqa: E712
    ).first()


def _spent_by_payer(session: Session, category_id: int, start, end) -> list[dict]:
    rows = session.exec(
        select(
            Transaction.payer_id,
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .where(
            Transaction.category_id == category_id,
            Transaction.type == TxnType.expense,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .group_by(Transaction.payer_id)
    ).all()

    names = {
        m.id: m.name for m in session.exec(select(Member)).all()
    }
    out = [
        {
            "member_id": payer_id,
            "name": names.get(payer_id, "미지정") if payer_id else "미지정",
            "amount": int(amount),
        }
        for payer_id, amount in rows
        if amount
    ]
    return sorted(out, key=lambda r: -r["amount"])


def compute_status(session: Session, month: str) -> dict | None:
    """해당 월 공유 예산 현황. 공유 카테고리나 예산이 없으면 None."""
    category = get_shared_category(session)
    if category is None:
        return None

    budget = session.exec(
        select(Budget).where(
            Budget.category_id == category.id, Budget.period_month == month
        )
    ).first()
    if budget is None:
        return None

    start, end = month_range(month)
    spent = session.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.category_id == category.id,
            Transaction.type == TxnType.expense,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
    ).one()
    if not isinstance(spent, int):
        spent = spent[0]

    usage = round(spent / budget.amount, 4) if budget.amount else None
    if usage is None:
        state = "unknown"
    elif usage >= 1:
        state = "over"
    elif usage >= WARN_RATIO:
        state = "warning"
    else:
        state = "ok"

    return {
        "month": month,
        "category_id": category.id,
        "category_name": category.name,
        "limit": budget.amount,
        "spent": spent,
        "remaining": budget.amount - spent,
        "usage": usage,
        "usage_percent": round(usage * 100, 1) if usage is not None else None,
        "state": state,
        "by_payer": _spent_by_payer(session, category.id, start, end),
    }


def crosses_warning(previous_spent: int, status: dict) -> bool:
    """이번 지출 때문에 '처음으로' 경고선을 넘었는지.

    넘은 뒤 매 건마다 경고가 울리면 소음이 되므로, 직전 상태가 경고선 아래였을 때만 True.
    """
    limit = status["limit"]
    if not limit:
        return False
    was = previous_spent / limit
    now = status["usage"]
    return was < WARN_RATIO <= now
