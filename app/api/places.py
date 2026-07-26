from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models.lifelog import Place
from app.schemas import PlaceCreate, PlaceRead, PlaceUpdate
from app.services import geocode

router = APIRouter(prefix="/places", tags=["places"])


@router.post("", response_model=PlaceRead, status_code=201)
def create_place(payload: PlaceCreate, session: Session = Depends(get_session)) -> Place:
    data = payload.model_dump()
    # 좌표 미지정 + 카카오 키 있으면 상호명으로 자동 지오코딩
    if data.get("lat") is None and data.get("lng") is None:
        hit = geocode.geocode_place(data["name"])
        if hit:
            for field in ("address", "region", "lat", "lng", "kakao_place_id"):
                if data.get(field) is None and hit.get(field) is not None:
                    data[field] = hit[field]
    obj = Place(**data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


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
