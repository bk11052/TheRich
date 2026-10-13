"""공유 예산을 함께 쓰는 사람 관리.

텔레그램 chat_id 를 사람에 매핑하는 곳이기도 하다 — 봇은 여기 등록된 chat_id 만 받는다.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_owner
from app.models.core import Member
from app.schemas import MemberCreate, MemberRead, MemberUpdate

router = APIRouter(prefix="/members", tags=["members"], dependencies=[Depends(require_owner)])


@router.post("", response_model=MemberRead, status_code=201)
def create_member(payload: MemberCreate, session: Session = Depends(get_session)) -> Member:
    if payload.telegram_chat_id is not None:
        dup = session.exec(
            select(Member).where(Member.telegram_chat_id == payload.telegram_chat_id)
        ).first()
        if dup:
            raise HTTPException(409, "이미 등록된 telegram_chat_id 입니다")
    obj = Member(**payload.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("", response_model=list[MemberRead])
def list_members(
    active_only: bool = True, session: Session = Depends(get_session)
) -> list[Member]:
    q = select(Member)
    if active_only:
        q = q.where(Member.active == True)  # noqa: E712
    return list(session.exec(q.order_by(Member.id)).all())


@router.get("/{member_id}", response_model=MemberRead)
def get_member(member_id: int, session: Session = Depends(get_session)) -> Member:
    obj = session.get(Member, member_id)
    if not obj:
        raise HTTPException(404, "member not found")
    return obj


@router.patch("/{member_id}", response_model=MemberRead)
def update_member(
    member_id: int, payload: MemberUpdate, session: Session = Depends(get_session)
) -> Member:
    obj = session.get(Member, member_id)
    if not obj:
        raise HTTPException(404, "member not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Member, member_id)
    if not obj:
        raise HTTPException(404, "member not found")
    session.delete(obj)
    session.commit()
