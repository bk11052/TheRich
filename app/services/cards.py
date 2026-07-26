"""카드 혜택 분석 — 이번 달 실적, 카테고리별 최적 카드."""

from sqlmodel import Session, select

from app.models.base import TxnType
from app.models.cards import Card, CardBenefit
from app.models.core import Category, Transaction
from app.services.period import month_range


def monthly_spend(session: Session, account_id: int | None, month: str) -> int:
    """해당 카드 계좌의 이번 달 지출 합(실적)."""
    if account_id is None:
        return 0
    start, end = month_range(month)
    rows = session.exec(
        select(Transaction).where(
            Transaction.account_id == account_id,
            Transaction.type == TxnType.expense,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
    ).all()
    return sum(t.amount for t in rows)


def _category_names(session: Session) -> dict[int, str]:
    return {c.id: c.name for c in session.exec(select(Category)).all()}


def card_status_list(session: Session, month: str) -> list[dict]:
    """활성 카드별 실적 + 혜택 목록."""
    cat_names = _category_names(session)
    cards = session.exec(
        select(Card).where(Card.active == True).order_by(Card.sort_order, Card.id)  # noqa: E712
    ).all()
    result = []
    for card in cards:
        benefits = session.exec(
            select(CardBenefit).where(CardBenefit.card_id == card.id)
        ).all()
        spend = monthly_spend(session, card.account_id, month)
        threshold = card.performance_threshold
        result.append(
            {
                "id": card.id,
                "name": card.name,
                "issuer": card.issuer,
                "account_id": card.account_id,
                "performance_threshold": threshold,
                "annual_fee": card.annual_fee,
                "active": card.active,
                "monthly_spend": spend,
                "threshold_met": (threshold is None) or (spend >= threshold),
                "benefits": [
                    {
                        "id": b.id,
                        "category_id": b.category_id,
                        "category_name": cat_names.get(b.category_id, "전체")
                        if b.category_id
                        else "전체",
                        "kind": b.kind,
                        "rate_bp": b.rate_bp,
                        "monthly_cap": b.monthly_cap,
                        "note": b.note,
                    }
                    for b in sorted(benefits, key=lambda x: -x.rate_bp)
                ],
            }
        )
    return result


def best_by_category(session: Session) -> list[dict]:
    """카테고리별로 적립/할인율이 가장 높은 카드. (전체 혜택은 '전체' 항목으로.)"""
    cat_names = _category_names(session)
    active_ids = {
        c.id for c in session.exec(select(Card).where(Card.active == True)).all()  # noqa: E712
    }
    card_names = {c.id: c.name for c in session.exec(select(Card)).all()}

    best: dict[int | None, dict] = {}
    for b in session.exec(select(CardBenefit)).all():
        if b.card_id not in active_ids:
            continue
        cur = best.get(b.category_id)
        if cur is None or b.rate_bp > cur["rate_bp"]:
            best[b.category_id] = {
                "category_id": b.category_id,
                "category_name": cat_names.get(b.category_id, "전체")
                if b.category_id
                else "전체",
                "card_id": b.card_id,
                "card_name": card_names.get(b.card_id, "?"),
                "kind": b.kind,
                "rate_bp": b.rate_bp,
                "note": b.note,
            }
    # 전체(None) 먼저, 그다음 rate 높은 순
    return sorted(
        best.values(), key=lambda x: (x["category_id"] is not None, -x["rate_bp"])
    )
