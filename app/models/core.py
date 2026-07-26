from datetime import date, datetime

from sqlmodel import Field, SQLModel

from app.models.base import (
    AccountSide,
    AccountType,
    CategoryKind,
    MatchType,
    TimestampMixin,
    TxnSource,
    TxnType,
)

# 각 엔티티는 *Base(공유 필드, 비-테이블) + 테이블 모델로 구성.
# API 입출력 스키마(Create/Read/Update)는 app/schemas.py 가 *Base 를 상속해 정의.


# ---------- Account ----------
class AccountBase(SQLModel):
    name: str
    type: AccountType
    side: AccountSide
    currency: str = Field(default="KRW", max_length=3)
    balance: int = 0  # 최소단위 정수(원). 증권은 Phase 2에서 토스 API 자동.
    institution: str | None = None
    is_manual: bool = True
    sort_order: int = 0
    archived: bool = False


class Account(AccountBase, TimestampMixin, table=True):
    __tablename__ = "account"
    id: int | None = Field(default=None, primary_key=True)


# ---------- Category ----------
class CategoryBase(SQLModel):
    name: str
    parent_id: int | None = Field(default=None, foreign_key="category.id")
    kind: CategoryKind = CategoryKind.expense
    icon: str | None = None
    color: str | None = None
    is_fixed: bool = False  # 고정지출 힌트
    sort_order: int = 0


class Category(CategoryBase, TimestampMixin, table=True):
    __tablename__ = "category"
    id: int | None = Field(default=None, primary_key=True)


# ---------- CategoryRule ----------
class CategoryRuleBase(SQLModel):
    match_type: MatchType = MatchType.contains
    pattern: str
    category_id: int = Field(foreign_key="category.id")
    priority: int = 0
    enabled: bool = True


class CategoryRule(CategoryRuleBase, TimestampMixin, table=True):
    __tablename__ = "category_rule"
    id: int | None = Field(default=None, primary_key=True)


# ---------- Transaction ----------
class TransactionBase(SQLModel):
    account_id: int = Field(foreign_key="account.id", index=True)
    counter_account_id: int | None = Field(default=None, foreign_key="account.id")
    type: TxnType
    amount: int  # 최소단위 정수(원)
    currency: str = Field(default="KRW", max_length=3)
    occurred_at: datetime = Field(index=True)
    merchant: str | None = None
    category_id: int | None = Field(default=None, foreign_key="category.id", index=True)
    memo: str | None = None
    source: TxnSource = TxnSource.manual
    place_id: int | None = Field(default=None, foreign_key="place.id")


class Transaction(TransactionBase, TimestampMixin, table=True):
    __tablename__ = "transaction"
    id: int | None = Field(default=None, primary_key=True)


# ---------- Budget ----------
class BudgetBase(SQLModel):
    category_id: int = Field(foreign_key="category.id")
    period_month: str = Field(index=True)  # "YYYY-MM"
    amount: int


class Budget(BudgetBase, TimestampMixin, table=True):
    __tablename__ = "budget"
    id: int | None = Field(default=None, primary_key=True)


# ---------- NetWorthSnapshot ----------
class NetWorthSnapshot(SQLModel, table=True):
    """순자산 추이용 월 스냅샷 (account 잔액에서 집계)."""

    __tablename__ = "net_worth_snapshot"

    id: int | None = Field(default=None, primary_key=True)
    snapshot_date: date = Field(index=True)
    total_assets: int
    total_liabilities: int
    net_worth: int
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
