from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """created_at / updated_at 컬럼을 제공하는 비-테이블 믹스인."""

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class AccountType(str, Enum):
    bank = "bank"
    card = "card"
    cash = "cash"
    securities = "securities"
    investment = "investment"
    real_estate = "real_estate"
    pension = "pension"
    loan = "loan"
    deposit = "deposit"
    other = "other"


class AccountSide(str, Enum):
    asset = "asset"
    liability = "liability"


class TxnType(str, Enum):
    expense = "expense"
    income = "income"
    transfer = "transfer"


class TxnSource(str, Enum):
    telegram_ocr = "telegram_ocr"
    manual = "manual"
    csv = "csv"
    toss_api = "toss_api"


class CategoryKind(str, Enum):
    expense = "expense"
    income = "income"


class MatchType(str, Enum):
    contains = "contains"
    regex = "regex"
    exact = "exact"


class BenefitKind(str, Enum):
    accrue = "accrue"  # 적립
    discount = "discount"  # 할인
