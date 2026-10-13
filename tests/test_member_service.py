"""멤버 조회(봇 허용목록) + 색 정규화."""

import pytest
from sqlmodel import Session

from app.services.members import (
    DEFAULT_PALETTE,
    next_unused_color,
    normalize_color,
    resolve_by_chat_id,
)


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


@pytest.mark.parametrize("raw, expected", [
    ("#FF0000", "#ff0000"),
    ("ff0000", "#ff0000"),
    ("#f00", "#ff0000"),
    ("f00", "#ff0000"),
    ("빨강", "#e5484d"),
    ("  파랑  ", "#2f6df6"),
    ("BLUE", "#2f6df6"),
])
def test_normalize_color_accepts_hex_and_aliases(raw, expected):
    assert normalize_color(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "무지개", "#12345", "zzzzzz", "#1234567"])
def test_normalize_color_rejects_garbage(raw):
    assert normalize_color(raw) is None


def test_next_unused_color_skips_taken_ones(session: Session, make_member):
    m = make_member("나", chat_id=111)
    m.color = DEFAULT_PALETTE[0]
    session.add(m)
    session.commit()

    assert next_unused_color(session) == DEFAULT_PALETTE[1]


def test_next_unused_color_wraps_when_palette_exhausted(session: Session, make_member):
    for i, color in enumerate(DEFAULT_PALETTE):
        m = make_member(f"사람{i}", chat_id=1000 + i)
        m.color = color
        session.add(m)
    session.commit()

    assert next_unused_color(session) == DEFAULT_PALETTE[0]
