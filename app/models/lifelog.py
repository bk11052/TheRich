from datetime import datetime

from sqlmodel import Field, SQLModel


class Place(SQLModel, table=True):
    """장소(맛집/추억 기록). 상호명 → 카카오 로컬 API 로 주소·좌표 채움."""

    __tablename__ = "place"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    region: str | None = None  # 동네
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    kakao_place_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Photo(SQLModel, table=True):
    """거래에 첨부하는 사진(음식 등). 웹 파일선택으로 업로드."""

    __tablename__ = "photo"

    id: int | None = Field(default=None, primary_key=True)
    transaction_id: int | None = Field(
        default=None, foreign_key="transaction.id", index=True
    )
    file_path: str
    taken_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Tag(SQLModel, table=True):
    """거래 태그(회식/데이트/가족 등)."""

    __tablename__ = "tag"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    color: str | None = None


class TransactionTag(SQLModel, table=True):
    """거래 ↔ 태그 M:N 연결."""

    __tablename__ = "transaction_tag"

    transaction_id: int = Field(foreign_key="transaction.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
