"""멤버 조회.

텔레그램 핸들러가 얇게 유지되도록, 판단이 들어가는 부분은 여기에 둔다.
"""

from sqlmodel import Session, select

from app.models.core import Member


def resolve_by_chat_id(session: Session, chat_id: int) -> Member | None:
    """등록된 활성 멤버만 돌려준다. 봇의 허용목록 역할."""
    return session.exec(
        select(Member).where(
            Member.telegram_chat_id == chat_id,
            Member.active == True,  # noqa: E712
        )
    ).first()
