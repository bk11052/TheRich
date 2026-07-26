from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.core import CategoryRule
from app.schemas import CategoryRuleCreate, CategoryRuleRead, CategoryRuleUpdate

router = APIRouter(prefix="/category-rules", tags=["category-rules"])


@router.post("", response_model=CategoryRuleRead, status_code=201)
def create_rule(
    payload: CategoryRuleCreate, session: Session = Depends(get_session)
) -> CategoryRule:
    obj = CategoryRule(**payload.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("", response_model=list[CategoryRuleRead])
def list_rules(session: Session = Depends(get_session)) -> list[CategoryRule]:
    return list(
        session.exec(
            select(CategoryRule).order_by(CategoryRule.priority.desc(), CategoryRule.id)
        ).all()
    )


@router.get("/{rule_id}", response_model=CategoryRuleRead)
def get_rule(rule_id: int, session: Session = Depends(get_session)) -> CategoryRule:
    obj = session.get(CategoryRule, rule_id)
    if not obj:
        raise HTTPException(404, "rule not found")
    return obj


@router.patch("/{rule_id}", response_model=CategoryRuleRead)
def update_rule(
    rule_id: int, payload: CategoryRuleUpdate, session: Session = Depends(get_session)
) -> CategoryRule:
    obj = session.get(CategoryRule, rule_id)
    if not obj:
        raise HTTPException(404, "rule not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(CategoryRule, rule_id)
    if not obj:
        raise HTTPException(404, "rule not found")
    session.delete(obj)
    session.commit()
