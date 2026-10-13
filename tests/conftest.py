"""공용 테스트 픽스처.

실제 DB(therich.db)를 건드리지 않도록 테스트마다 **메모리 SQLite**를 새로 만들고,
FastAPI 의존성 오버라이드로 라우터가 그 세션을 쓰게 바꾼다.
테스트 간 상태가 섞이지 않으므로 실행 순서에 의존하지 않는다.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  모든 테이블을 metadata 에 등록시키기 위한 import
from app.db import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    # sqlite:// = 파일 없는 메모리 DB.
    # StaticPool 을 써야 여러 커넥션이 같은 메모리 DB 를 공유한다(기본 풀은 커넥션마다 새 DB).
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    # with 문을 쓰지 않으면 lifespan(=APScheduler 기동)이 돌지 않는다. 테스트에 불필요.
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- 도메인 픽스처 ----------
# 테스트가 "무엇을 검증하는지"만 남도록, 준비 과정은 여기로 뺀다.

from app.models.base import AccountSide, AccountType, CategoryKind, MatchType  # noqa: E402
from app.models.core import Account, Category, CategoryRule  # noqa: E402


@pytest.fixture
def account(session: Session) -> Account:
    obj = Account(name="테스트 은행", type=AccountType.bank, side=AccountSide.asset, balance=1_000_000)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@pytest.fixture
def make_category(session: Session):
    def _make(name: str, kind: CategoryKind = CategoryKind.expense) -> Category:
        obj = Category(name=name, kind=kind)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    return _make


@pytest.fixture
def make_rule(session: Session):
    def _make(pattern: str, category_id: int, match_type: MatchType = MatchType.contains,
              priority: int = 0, enabled: bool = True) -> CategoryRule:
        obj = CategoryRule(
            pattern=pattern, category_id=category_id,
            match_type=match_type, priority=priority, enabled=enabled,
        )
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    return _make


from app.models.core import Member  # noqa: E402


@pytest.fixture
def make_member(session: Session):
    def _make(name: str, chat_id: int | None = None, is_self: bool = False) -> Member:
        obj = Member(name=name, telegram_chat_id=chat_id, is_self=is_self)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    return _make


@pytest.fixture
def date_budget(session: Session, client: TestClient):
    """공유 카테고리 '데이트' + 2026-10 한도 50만원. (category, limit) 반환."""
    cat = Category(name="데이트", is_shared=True)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    client.post("/budgets", json={
        "category_id": cat.id, "period_month": "2026-10", "amount": 500_000,
    })
    return cat, 500_000
