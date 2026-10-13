"""순자산 집계(app/services/networth.py) 테스트. 자산 - 부채 계산이 핵심."""

from sqlmodel import Session

from app.models.base import AccountSide, AccountType
from app.models.core import Account
from app.services.networth import compute_current


def _add(session: Session, name: str, balance: int, side: AccountSide,
         atype: AccountType = AccountType.bank, archived: bool = False):
    obj = Account(name=name, type=atype, side=side, balance=balance, archived=archived)
    session.add(obj)
    session.commit()
    return obj


def test_net_worth_is_assets_minus_liabilities(session: Session):
    _add(session, "은행", 3_000_000, AccountSide.asset)
    _add(session, "카드", 500_000, AccountSide.liability, AccountType.card)

    result = compute_current(session)

    assert result["total_assets"] == 3_000_000
    assert result["total_liabilities"] == 500_000
    assert result["net_worth"] == 2_500_000


def test_archived_accounts_are_excluded(session: Session):
    _add(session, "현역 계좌", 1_000_000, AccountSide.asset)
    _add(session, "해지한 계좌", 9_000_000, AccountSide.asset, archived=True)

    assert compute_current(session)["net_worth"] == 1_000_000


def test_allocation_groups_assets_by_type(session: Session):
    _add(session, "은행A", 1_000_000, AccountSide.asset, AccountType.bank)
    _add(session, "은행B", 2_000_000, AccountSide.asset, AccountType.bank)
    _add(session, "증권", 5_000_000, AccountSide.asset, AccountType.securities)

    by_type = compute_current(session)["by_type"]

    assert by_type[0]["key"] == "securities"   # 금액 큰 순 정렬
    assert by_type[0]["amount"] == 5_000_000
    assert by_type[1]["key"] == "bank"
    assert by_type[1]["amount"] == 3_000_000   # 같은 type 끼리 합산


def test_zero_balance_type_is_omitted_from_allocation(session: Session):
    _add(session, "잔액 있는 계좌", 1_000_000, AccountSide.asset, AccountType.bank)
    _add(session, "빈 계좌", 0, AccountSide.asset, AccountType.cash)

    keys = [row["key"] for row in compute_current(session)["by_type"]]

    assert "cash" not in keys


def test_empty_db_returns_zeros_not_error(session: Session):
    result = compute_current(session)

    assert result["net_worth"] == 0
    assert result["by_type"] == []
