from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.config import settings

# SQLite는 스레드 체크 옵션 필요 (FastAPI 멀티스레드 대비)
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
