from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.core import Category
from app.schemas import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryRead, status_code=201)
def create_category(payload: CategoryCreate, session: Session = Depends(get_session)) -> Category:
    obj = Category(**payload.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)) -> list[Category]:
    return list(
        session.exec(select(Category).order_by(Category.sort_order, Category.id)).all()
    )


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, session: Session = Depends(get_session)) -> Category:
    obj = session.get(Category, category_id)
    if not obj:
        raise HTTPException(404, "category not found")
    return obj


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int, payload: CategoryUpdate, session: Session = Depends(get_session)
) -> Category:
    obj = session.get(Category, category_id)
    if not obj:
        raise HTTPException(404, "category not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Category, category_id)
    if not obj:
        raise HTTPException(404, "category not found")
    session.delete(obj)
    session.commit()
