"""멤버 조회·색 관리.

텔레그램 핸들러가 얇게 유지되도록, 판단이 들어가는 부분은 전부 여기에 둔다.
"""

import re

from sqlmodel import Session, select

from app.models.core import Member

# 대시보드에서 서로 잘 구분되고 라이트/다크 모두에서 읽히는 색.
DEFAULT_PALETTE = ("#2f6df6", "#e5484d", "#2e9e5b", "#b05cd6", "#e08c00", "#0f9fb0")

# 텔레그램에서 색을 말로 지정할 수 있게 하는 별칭.
COLOR_ALIASES = {
    "파랑": "#2f6df6", "파란": "#2f6df6", "blue": "#2f6df6",
    "빨강": "#e5484d", "빨간": "#e5484d", "red": "#e5484d",
    "초록": "#2e9e5b", "녹색": "#2e9e5b", "green": "#2e9e5b",
    "보라": "#b05cd6", "purple": "#b05cd6",
    "주황": "#e08c00", "노랑": "#e08c00", "orange": "#e08c00",
    "청록": "#0f9fb0", "teal": "#0f9fb0",
}

_HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def resolve_by_chat_id(session: Session, chat_id: int) -> Member | None:
    """등록된 활성 멤버만 돌려준다. 봇의 허용목록 역할."""
    return session.exec(
        select(Member).where(
            Member.telegram_chat_id == chat_id,
            Member.active == True,  # noqa: E712
        )
    ).first()


def normalize_color(raw: str | None) -> str | None:
    """'빨강' / 'f00' / '#FF0000' → '#ff0000'. 못 알아들으면 None."""
    if not raw:
        return None
    text = raw.strip().lower()
    if text in COLOR_ALIASES:
        return COLOR_ALIASES[text]
    m = _HEX.match(text)
    if not m:
        return None
    value = m.group(1)
    if len(value) == 3:  # #abc → #aabbcc
        value = "".join(ch * 2 for ch in value)
    return "#" + value.lower()


def next_unused_color(session: Session) -> str:
    """팔레트에서 아직 아무도 안 쓴 색. 다 쓰면 처음으로 돌아간다."""
    used = {
        m.color for m in session.exec(select(Member)).all() if m.color
    }
    for color in DEFAULT_PALETTE:
        if color not in used:
            return color
    return DEFAULT_PALETTE[0]
