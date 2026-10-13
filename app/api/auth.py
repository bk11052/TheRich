"""로그인·로그아웃·내 정보."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel import Session as DbSession
from sqlmodel import select
from sqlmodel import SQLModel

from app.db import get_session
from app.deps import current_member, require_member
from app.models.core import Member
from app.schemas import MemberRead
from app.services import login_throttle
from app.services.auth import (
    SESSION_COOKIE,
    SESSION_TTL,
    create_session,
    revoke_session,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(SQLModel):
    name: str
    password: str


@router.post("/login", response_model=MemberRead)
def login(
    payload: LoginPayload,
    request: Request,
    response: Response,
    db: DbSession = Depends(get_session),
) -> Member:
    ip = request.client.host if request.client else None
    wait = login_throttle.seconds_locked(ip, payload.name)
    if wait:
        raise HTTPException(
            429,
            f"로그인 시도가 너무 많아요. {wait // 60 + 1}분 뒤에 다시 시도하세요.",
            headers={"Retry-After": str(wait)},
        )

    member = db.exec(
        select(Member).where(
            Member.name == payload.name,
            Member.active == True,  # noqa: E712
        )
    ).first()
    # 이름이 없는 경우와 비밀번호가 틀린 경우를 구분해서 알려주지 않는다
    # (존재하는 계정 이름을 떠볼 수 있게 되므로).
    if member is None or not verify_password(payload.password, member.password_hash):
        # 없는 이름도 똑같이 센다. 아니면 '잠기는 이름 = 존재하는 이름'으로 떠볼 수 있다.
        login_throttle.record_failure(ip, payload.name)
        raise HTTPException(401, "이름 또는 비밀번호가 올바르지 않습니다")

    login_throttle.reset(ip, payload.name)
    token = create_session(db, member)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,   # JS 에서 못 읽게 — XSS 로 토큰이 새는 경로를 막는다
        samesite="lax",
        path="/",
    )
    return member


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    _member: Member = Depends(require_member),
    db: DbSession = Depends(get_session),
) -> None:
    # 쿠키만 지우면 서버의 세션 행은 살아있으므로 둘 다 지운다.
    revoke_session(db, request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=MemberRead)
def me(member: Member = Depends(require_member)) -> Member:
    return member


@router.get("/status")
def status(member: Member | None = Depends(current_member)) -> dict:
    """로그인 화면이 '지금 로그인돼 있나'를 묻는 용도. 미인증도 200 으로 답한다."""
    if member is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "id": member.id,
        "name": member.name,
        "role": member.role.value,
        "color": member.color,
    }
