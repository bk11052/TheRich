from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_owner
from app.models.lifelog import Place
from app.schemas import PlaceCreate, PlaceRead, PlaceUpdate
from app.services import geocode
from app.services.lifelog import create_place as make_place

router = APIRouter(prefix="/places", tags=["places"], dependencies=[Depends(require_owner)])


@router.post("", response_model=PlaceRead, status_code=201)
def create_place(payload: PlaceCreate, session: Session = Depends(get_session)) -> Place:
    return make_place(session, payload.model_dump())


@router.get("/search")
def search_places(q: str = Query(..., min_length=1)) -> list[dict]:
    """카카오 로컬 키워드 검색 (자동완성용). 키 없으면 빈 배열."""
    return geocode.search_places(q)


@router.get("", response_model=list[PlaceRead])
def list_places(
    q: str | None = None, session: Session = Depends(get_session)
) -> list[Place]:
    query = select(Place)
    if q:
        query = query.where(Place.name.contains(q))  # type: ignore[attr-defined]
    return list(session.exec(query.order_by(Place.name)).all())


@router.get("/{place_id}", response_model=PlaceRead)
def get_place(place_id: int, session: Session = Depends(get_session)) -> Place:
    obj = session.get(Place, place_id)
    if not obj:
        raise HTTPException(404, "place not found")
    return obj


@router.patch("/{place_id}", response_model=PlaceRead)
def update_place(
    place_id: int, payload: PlaceUpdate, session: Session = Depends(get_session)
) -> Place:
    obj = session.get(Place, place_id)
    if not obj:
        raise HTTPException(404, "place not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{place_id}", status_code=204)
def delete_place(place_id: int, session: Session = Depends(get_session)) -> None:
    obj = session.get(Place, place_id)
    if not obj:
        raise HTTPException(404, "place not found")
    session.delete(obj)
    session.commit()
