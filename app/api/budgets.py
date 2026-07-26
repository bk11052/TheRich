from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models.base import TxnType
from app.models.core import Budget, Transaction
from app.schemas import BudgetCreate, BudgetRead, BudgetUpdate
from app.services.period import month_range

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetRead, status_code=201)
def create_budget(payload: BudgetCreate, session: Session = Depends(get_session)) -> Budget:
    obj = Budget(**payload.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    month: str | None = None, session: Session = Depends(get_session)
) -> list[Budget]:
    q = select(Budget)
    if month:
        q = q.where(Budget.period_month == month)
    return list(session.exec(q.order_by(Budget.id)).all())


# 주의: /{budget_id} 보다 먼저 선언해야 "status"가 id로 해석되지 않음
@router.get("/status")
def budget_status(
    month: str = Query(..., description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> list[dict]:
    """해당 월 예산별 소진율 = 카테고리 지출 합 / 예산."""
    start, end = month_range(month)
    budgets = session.exec(select(Budget).where(Budget.period_month == month)).all()
    out: list[dict] = []
    for b in budgets:
        spent = session.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.category_id == b.category_id,
                Transaction.type == TxnType.expense,
                Transaction.occurred_at >= start,
                Transaction.occurred_at < end,
            )
        ).one()
        if not isinstance(spent, int):
            spent = spent[0]
        out.append(
            {
                "budget_id": b.id,
                "category_id": b.category_id,
                "period_month": b.period_month,
                "amount": b.amount,
                "spent": spent,
                "remaining": b.amount - spent,
                "usage": round(spent / b.amount, 3) if b.amount else None,
            }
        )
    return out


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(budget_id: int, session: Session = Depends(get_session)) -> Budget:
    obj = session.get(Budget, budget_id)
    if not obj:
        raise HTTPException(404, "budget not found")
    return obj


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int, payload: BudgetUpdate, session: Session = Depends(get_session)
) -> Budget:
    obj = session.get(Budget, budget_id)
    if not obj:
        raise HTTPException(404, "budget not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Budget, budget_id)
    if not obj:
        raise HTTPException(404, "budget not found")
    session.delete(obj)
    session.commit()
