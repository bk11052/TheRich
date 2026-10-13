from datetime import date, datetime

from sqlmodel import Field, SQLModel

from app.models.base import (
    AccountSide,
    AccountType,
    CategoryKind,
    MatchType,
    MemberRole,
    TimestampMixin,
    TxnSource,
    TxnType,
)

# 각 엔티티는 *Base(공유 필드, 비-테이블) + 테이블 모델로 구성.
# API 입출력 스키마(Create/Read/Update)는 app/schemas.py 가 *Base 를 상속해 정의.


# ---------- Member ----------
# 공유 예산을 함께 쓰는 사람. 텔레그램 chat_id 를 사람에 매핑하는 역할도 겸한다
# (등록되지 않은 chat_id 는 봇이 거절 — 봇 username 만 알면 누구나 말을 걸 수 있으므로).
class MemberBase(SQLModel):
    name: str
    telegram_chat_id: int | None = Field(default=None, index=True, unique=True)
    is_self: bool = False  # 앱 주인 본인
    # 대시보드·요약에서 사람을 구분하는 색(#RRGGBB). 텔레그램 /color 로도 바꾼다.
    color: str | None = None
    # 접근 범위. owner 만 자산·거래 전체를 볼 수 있고 partner 는 공유 예산만 본다.
    role: MemberRole = MemberRole.partner
    active: bool = True


class Member(MemberBase, TimestampMixin, table=True):
    __tablename__ = "member"
    id: int | None = Field(default=None, primary_key=True)
    # 로그인 비밀번호. 스키마(MemberRead)에 없으므로 API 로 새어나가지 않는다.
    password_hash: str | None = Field(default=None, exclude=True)


class Session(TimestampMixin, table=True):
    """로그인 세션. 토큰 원문이 아니라 해시만 저장해 DB 가 새도 세션을 못 쓰게 한다."""

    __tablename__ = "session"
    id: int | None = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key="member.id", index=True)
    token_hash: str = Field(index=True, unique=True)
    expires_at: datetime = Field(index=True)


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
    # 둘이 함께 쓰는 예산인지(데이트비용 등). 이 카테고리의 Budget 이 공유 한도가 된다.
    is_shared: bool = False
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
    # 공유 지출에서 실제로 결제한 사람. 정산은 하지 않고 기여 내역만 보여준다.
    payer_id: int | None = Field(default=None, foreign_key="member.id", index=True)


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
