"""순자산 집계 — account 잔액에서 실시간 계산.

증권/투자 계좌는 Phase 2에서 토스 API가 balance 를 자동 갱신하면 그대로 반영된다.
"""

import calendar
from datetime import date

from sqlmodel import Session, select

from app.models.base import AccountSide, AccountType
from app.models.core import Account, NetWorthSnapshot

# 자산배분 표시용 한글 라벨
TYPE_LABEL: dict[AccountType, str] = {
    AccountType.bank: "예금",
    AccountType.card: "카드",
    AccountType.cash: "현금",
    AccountType.securities: "증권",
    AccountType.investment: "투자",
    AccountType.real_estate: "부동산",
    AccountType.pension: "연금",
    AccountType.loan: "대출",
    AccountType.deposit: "적금",
    AccountType.other: "기타",
}


def _active_accounts(session: Session) -> list[Account]:
    return list(
        session.exec(select(Account).where(Account.archived == False)).all()  # noqa: E712
    )


def compute_current(session: Session) -> dict:
    """활성 계좌 잔액으로 현재 순자산 + 자산배분 집계."""
    accounts = _active_accounts(session)
    assets = [a for a in accounts if a.side == AccountSide.asset]
    liabilities = [a for a in accounts if a.side == AccountSide.liability]

    total_assets = sum(a.balance for a in assets)
    total_liabilities = sum(a.balance for a in liabilities)

    # 자산배분: 자산 계좌를 type 별로 합산 (금액 큰 순)
    by_type_amount: dict[AccountType, int] = {}
    for a in assets:
        by_type_amount[a.type] = by_type_amount.get(a.type, 0) + a.balance
    by_type = [
        {"key": t.value, "label": TYPE_LABEL.get(t, t.value), "amount": amt}
        for t, amt in sorted(by_type_amount.items(), key=lambda x: -x[1])
        if amt != 0
    ]

    # 계좌별 상세 (자산+부채 모두, 잔액 큰 순)
    by_account = [
        {
            "account_id": a.id,
            "name": a.name,
            "type": a.type.value,
            "side": a.side.value,
            "balance": a.balance,
        }
        for a in sorted(accounts, key=lambda x: -x.balance)
    ]

    return {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "net_worth": total_assets - total_liabilities,
        "by_type": by_type,
        "by_account": by_account,
    }


def month_end(d: date) -> date:
    """해당 월의 마지막 날. 스냅샷은 항상 월말 날짜로 저장(월 1개)."""
    last = calendar.monthrange(d.year, d.month)[1]
    return date(d.year, d.month, last)


def ensure_month_snapshot(session: Session, today: date | None = None) -> bool:
    """이번 달 스냅샷이 하나도 없으면 월말 날짜로 캡처. 캡처했으면 True.

    서버 시작 시 호출 — 24/7이 아닌 환경에서 '말일에 서버가 꺼져 있어 스냅샷을
    통째로 놓치는' 구멍을 메운다. 이미 있으면 건드리지 않음.
    """
    today = today or date.today()
    month_start = date(today.year, today.month, 1)
    exists = session.exec(
        select(NetWorthSnapshot).where(NetWorthSnapshot.snapshot_date >= month_start)
    ).first()
    if exists:
        return False
    capture_snapshot(session, month_end(today))
    return True


def capture_snapshot(session: Session, snapshot_date: date) -> NetWorthSnapshot:
    """현재 순자산을 해당 날짜 스냅샷으로 저장(같은 날짜면 갱신)."""
    current = compute_current(session)
    existing = session.exec(
        select(NetWorthSnapshot).where(NetWorthSnapshot.snapshot_date == snapshot_date)
    ).first()
    if existing:
        existing.total_assets = current["total_assets"]
        existing.total_liabilities = current["total_liabilities"]
        existing.net_worth = current["net_worth"]
        snap = existing
    else:
        snap = NetWorthSnapshot(
            snapshot_date=snapshot_date,
            total_assets=current["total_assets"],
            total_liabilities=current["total_liabilities"],
            net_worth=current["net_worth"],
        )
    session.add(snap)
    session.commit()
    session.refresh(snap)
    return snap
