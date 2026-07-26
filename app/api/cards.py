from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models.cards import Card, CardBenefit
from app.schemas import (
    BestCard,
    CardBenefitCreate,
    CardBenefitRead,
    CardCreate,
    CardRead,
    CardStatus,
    CardUpdate,
)
from app.services import cards as cards_service

router = APIRouter(prefix="/cards", tags=["cards"])


def _current_month() -> str:
    return datetime.now().strftime("%Y-%m")


# ---------- 조회(합성) — 정적 경로를 /{card_id} 보다 먼저 ----------
@router.get("", response_model=list[CardStatus])
def list_cards(
    month: str | None = Query(None, description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> list[dict]:
    return cards_service.card_status_list(session, month or _current_month())


@router.get("/best-by-category", response_model=list[BestCard])
def best_by_category(session: Session = Depends(get_session)) -> list[dict]:
    return cards_service.best_by_category(session)


# ---------- 카드 CRUD ----------
@router.post("", response_model=CardRead, status_code=201)
def create_card(payload: CardCreate, session: Session = Depends(get_session)) -> Card:
    obj = Card(**payload.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.patch("/{card_id}", response_model=CardRead)
def update_card(
    card_id: int, payload: CardUpdate, session: Session = Depends(get_session)
) -> Card:
    obj = session.get(Card, card_id)
    if not obj:
        raise HTTPException(404, "card not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{card_id}", status_code=204)
def delete_card(card_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Card, card_id)
    if not obj:
        raise HTTPException(404, "card not found")
    # 딸린 혜택도 함께 삭제
    for b in session.exec(select(CardBenefit).where(CardBenefit.card_id == card_id)).all():
        session.delete(b)
    session.delete(obj)
    session.commit()


# ---------- 혜택 ----------
@router.post("/{card_id}/benefits", response_model=CardBenefitRead, status_code=201)
def add_benefit(
    card_id: int, payload: CardBenefitCreate, session: Session = Depends(get_session)
) -> CardBenefit:
    if not session.get(Card, card_id):
        raise HTTPException(404, "card not found")
    data = payload.model_dump()
    data["card_id"] = card_id  # 경로 우선
    obj = CardBenefit(**data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/benefits/{benefit_id}", status_code=204)
def delete_benefit(benefit_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(CardBenefit, benefit_id)
    if not obj:
        raise HTTPException(404, "benefit not found")
    session.delete(obj)
    session.commit()
