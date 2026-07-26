"""카드 혜택 최적화 — 보유 카드와 카테고리별 적립/할인 규칙.

Card 는 결제수단 계좌(account, type=card)와 선택적으로 연결(account_id)되어,
이번 달 실적(해당 계좌 지출 합)을 전월실적 기준(performance_threshold)과 비교한다.
CardBenefit 은 '카테고리 X 에서 rate_bp 만큼 적립/할인' 규칙.
"""

from sqlmodel import Field, SQLModel

from app.models.base import BenefitKind, TimestampMixin


class CardBase(SQLModel):
    name: str
    issuer: str | None = None
    account_id: int | None = Field(default=None, foreign_key="account.id")
    performance_threshold: int | None = None  # 전월실적 기준(원). None=조건없음
    annual_fee: int = 0
    active: bool = True
    sort_order: int = 0


class Card(CardBase, TimestampMixin, table=True):
    __tablename__ = "card"
    id: int | None = Field(default=None, primary_key=True)


class CardBenefitBase(SQLModel):
    card_id: int = Field(foreign_key="card.id", index=True)
    category_id: int | None = Field(
        default=None, foreign_key="category.id"
    )  # None = 전체 카테고리
    kind: BenefitKind = BenefitKind.accrue
    rate_bp: int  # basis points. 500 = 5%
    monthly_cap: int | None = None  # 월 적립/할인 한도(원)
    note: str | None = None


class CardBenefit(CardBenefitBase, TimestampMixin, table=True):
    __tablename__ = "card_benefit"
    id: int | None = Field(default=None, primary_key=True)
