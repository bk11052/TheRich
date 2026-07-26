"""API 입출력 스키마 (테이블 모델과 분리).

- *Create: 생성 입력 (id/타임스탬프 제외)
- *Read: 응답 (id + 타임스탬프 포함)
- *Update: 부분 수정 (모든 필드 Optional, PATCH 용)
"""

from datetime import date, datetime

from sqlmodel import SQLModel

from app.models.base import (
    AccountSide,
    AccountType,
    CategoryKind,
    MatchType,
    TxnSource,
    TxnType,
)
from app.models.core import (
    AccountBase,
    BudgetBase,
    CategoryBase,
    CategoryRuleBase,
    TransactionBase,
)


# ---------- Account ----------
class AccountCreate(AccountBase):
    pass


class AccountRead(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime


class AccountUpdate(SQLModel):
    name: str | None = None
    type: AccountType | None = None
    side: AccountSide | None = None
    currency: str | None = None
    balance: int | None = None
    institution: str | None = None
    is_manual: bool | None = None
    sort_order: int | None = None
    archived: bool | None = None


# ---------- Category ----------
class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CategoryUpdate(SQLModel):
    name: str | None = None
    parent_id: int | None = None
    kind: CategoryKind | None = None
    icon: str | None = None
    color: str | None = None
    is_fixed: bool | None = None
    sort_order: int | None = None


# ---------- CategoryRule ----------
class CategoryRuleCreate(CategoryRuleBase):
    pass


class CategoryRuleRead(CategoryRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CategoryRuleUpdate(SQLModel):
    match_type: MatchType | None = None
    pattern: str | None = None
    category_id: int | None = None
    priority: int | None = None
    enabled: bool | None = None


# ---------- Transaction ----------
class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime


class TransactionUpdate(SQLModel):
    account_id: int | None = None
    counter_account_id: int | None = None
    type: TxnType | None = None
    amount: int | None = None
    currency: str | None = None
    occurred_at: datetime | None = None
    merchant: str | None = None
    category_id: int | None = None
    memo: str | None = None
    source: TxnSource | None = None
    place_id: int | None = None


# ---------- Budget ----------
class BudgetCreate(BudgetBase):
    pass


class BudgetRead(BudgetBase):
    id: int
    created_at: datetime
    updated_at: datetime


class BudgetUpdate(SQLModel):
    category_id: int | None = None
    period_month: str | None = None
    amount: int | None = None


# ---------- NetWorth ----------
class AllocationSlice(SQLModel):
    key: str
    label: str
    amount: int


class AccountBalance(SQLModel):
    account_id: int
    name: str
    type: str
    side: str
    balance: int


class NetWorthCurrent(SQLModel):
    """계좌 잔액에서 실시간 집계한 현재 순자산."""

    total_assets: int
    total_liabilities: int
    net_worth: int
    by_type: list[AllocationSlice]
    by_account: list[AccountBalance]


class NetWorthSnapshotCreate(SQLModel):
    # 미지정이면 서버가 오늘 날짜로 캡처. 합계는 항상 서버가 계좌에서 계산.
    snapshot_date: date | None = None


class NetWorthSnapshotRead(SQLModel):
    id: int
    snapshot_date: date
    total_assets: int
    total_liabilities: int
    net_worth: int
    created_at: datetime


# ---------- Lifelog: Tag ----------
class TagCreate(SQLModel):
    name: str
    color: str | None = None


class TagRead(SQLModel):
    id: int
    name: str
    color: str | None = None


class TagUpdate(SQLModel):
    name: str | None = None
    color: str | None = None


# ---------- Lifelog: Place ----------
class PlaceCreate(SQLModel):
    name: str
    region: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    kakao_place_id: str | None = None


class PlaceRead(SQLModel):
    id: int
    name: str
    region: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    kakao_place_id: str | None = None
    created_at: datetime


class PlaceUpdate(SQLModel):
    name: str | None = None
    region: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    kakao_place_id: str | None = None


# ---------- Lifelog: Photo ----------
class PhotoRead(SQLModel):
    id: int
    transaction_id: int | None = None
    file_path: str  # 공개 경로 "/uploads/<파일명>"
    taken_at: datetime | None = None
    created_at: datetime


# ---------- Lifelog: Record (사진·장소·태그로 보강된 거래) ----------
class TransactionTagsSet(SQLModel):
    tag_ids: list[int]


class RecordRead(SQLModel):
    id: int  # transaction id
    type: TxnType
    amount: int
    occurred_at: datetime
    merchant: str | None = None
    memo: str | None = None
    category_id: int | None = None
    place: PlaceRead | None = None
    photos: list[PhotoRead] = []
    tags: list[TagRead] = []
