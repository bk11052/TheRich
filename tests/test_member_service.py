"""멤버 조회(봇 허용목록)."""

from sqlmodel import Session

from app.services.members import resolve_by_chat_id


def test_unregistered_chat_id_resolves_to_none(session: Session, make_member):
    make_member("나", chat_id=111)

    assert resolve_by_chat_id(session, 999) is None


def test_registered_chat_id_resolves(session: Session, make_member):
    me = make_member("나", chat_id=111)

    assert resolve_by_chat_id(session, 111).id == me.id


def test_inactive_member_is_rejected(session: Session, make_member):
    """비활성 멤버의 chat_id 는 더 이상 입력을 못 넣어야 한다."""
    m = make_member("헤어짐", chat_id=222)
    m.active = False
    session.add(m)
    session.commit()

    assert resolve_by_chat_id(session, 222) is None



