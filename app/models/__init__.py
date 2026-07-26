"""모든 SQLModel 테이블을 임포트해 SQLModel.metadata 에 등록한다.

Alembic env.py 가 `import app.models` 만 해도 전체 스키마를 인식하도록 하는 게 목적.
"""

from app.models.cards import Card, CardBenefit
from app.models.core import (
    Account,
    Budget,
    Category,
    CategoryRule,
    NetWorthSnapshot,
    Transaction,
)
from app.models.lifelog import Photo, Place, Tag, TransactionTag

__all__ = [
    "Account",
    "Category",
    "CategoryRule",
    "Transaction",
    "Budget",
    "NetWorthSnapshot",
    "Place",
    "Photo",
    "Tag",
    "TransactionTag",
    "Card",
    "CardBenefit",
]
