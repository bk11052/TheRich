"""인증 의존성.

기본값은 **owner 전용**이다. 라우터는 `require_owner` 를 걸어두고,
동반자에게 열어줄 소수의 경로만 `require_member` 로 낮춘다.
새 라우터를 추가했을 때 실수로 전부 공개되는 쪽이 아니라 막히는 쪽으로 기울게 하기 위함.
"""

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session as DbSession
from sqlmodel import select

from app.config import settings
from app.db import get_session
from app.models.base import MemberRole
from app.models.core import Member
from app.services.auth import SESSION_COOKIE, resolve_session


def _bearer(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    return value.strip() if scheme.lower() == "bearer" and value.strip() else None


def current_member(
    request: Request, db: DbSession = Depends(get_session)
) -> Member | None:
    """쿠키 세션 또는 서비스 토큰으로 사람을 식별한다. 못 하면 None."""
    token = _bearer(request)

    # 서비스 토큰(텔레그램 봇 등) → owner 권한. 사람 계정이 아니라 설정값으로 판단한다.
    if token and settings.service_token and token == settings.service_token:
        owner = db.exec(
            select(Member).where(
                Member.role == MemberRole.owner,
                Member.active == True,  # noqa: E712
            ).order_by(Member.id)
        ).first()
        if owner:
            return owner

    return resolve_session(db, request.cookies.get(SESSION_COOKIE) or token)


def require_member(member: Member | None = Depends(current_member)) -> Member:
    if member is None:
        raise HTTPException(401, "로그인이 필요합니다")
    return member


def require_owner(member: Member = Depends(require_member)) -> Member:
    if member.role != MemberRole.owner:
        raise HTTPException(403, "접근 권한이 없습니다")
    return member
