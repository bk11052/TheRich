from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.lifelog import Tag
from app.schemas import TagCreate, TagRead, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagRead, status_code=201)
def create_tag(payload: TagCreate, session: Session = Depends(get_session)) -> Tag:
    obj = Tag(**payload.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("", response_model=list[TagRead])
def list_tags(session: Session = Depends(get_session)) -> list[Tag]:
    return list(session.exec(select(Tag).order_by(Tag.id)).all())


@router.patch("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: int, payload: TagUpdate, session: Session = Depends(get_session)
) -> Tag:
    obj = session.get(Tag, tag_id)
    if not obj:
        raise HTTPException(404, "tag not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Tag, tag_id)
    if not obj:
        raise HTTPException(404, "tag not found")
    session.delete(obj)
    session.commit()
