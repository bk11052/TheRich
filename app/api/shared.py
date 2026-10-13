"""공유 예산(데이트비용) 현황 조회."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlmodel import Session, SQLModel, select

from app.db import get_session
from app.deps import require_member
from app.models.core import Member, Transaction
from app.models.lifelog import Photo, Place, Tag
from app.schemas import (
    PhotoRead,
    PlaceCreate,
    PlaceRead,
    RecordRead,
    TagCreate,
    TagRead,
    TransactionTagsSet,
)
from app.services import geocode
from app.services.lifelog import (
    RASTER_EXT,
    PhotoRejected,
    create_place,
    list_records,
    replace_tags,
    save_photo,
)
from app.services.members import normalize_color
from app.services.period import month_range
from app.services.shared_budget import compute_status, get_shared_category

router = APIRouter(
    prefix="/shared",
    tags=["shared"],
    # owner 와 partner 모두 접근 가능한 유일한 영역.
    dependencies=[Depends(require_member)],
)


@router.get("/budget")
def shared_budget_status(
    month: str = Query(..., description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> dict:
    status = compute_status(session, month)
    if status is None:
        raise HTTPException(
            404, "공유 예산이 설정되지 않았습니다 (is_shared 카테고리 + 해당 월 예산 필요)"
        )
    return status


@router.get("/members")
def shared_members(session: Session = Depends(get_session)) -> list[dict]:
    """공유 화면에서 사람을 색으로 구분하기 위한 최소 정보.

    telegram_chat_id·role 은 의도적으로 빼고 내려준다 — partner 가 볼 이유가 없다.
    """
    rows = session.exec(
        select(Member).where(Member.active == True).order_by(Member.id)  # noqa: E712
    ).all()
    return [{"id": m.id, "name": m.name, "color": m.color} for m in rows]


@router.get("/transactions")
def shared_transactions(
    month: str = Query(..., description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> list[dict]:
    """공유 카테고리 거래만. 개인 지출은 어떤 경우에도 섞이지 않는다."""
    category = get_shared_category(session)
    if category is None:
        return []
    start, end = month_range(month)
    rows = session.exec(
        select(Transaction)
        .where(
            Transaction.category_id == category.id,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .order_by(Transaction.occurred_at.desc())
    ).all()
    return [
        {
            "id": t.id,
            "amount": t.amount,
            "occurred_at": t.occurred_at.isoformat(),
            "merchant": t.merchant,
            "payer_id": t.payer_id,
            "source": t.source.value,
        }
        for t in rows
    ]


# ---------- 기록(사진·장소·태그) — 공유 거래에 한해서 ----------
# partner 는 데이트비용 거래의 기록만 보고 덧붙일 수 있다. 다른 거래 id 를 넣으면
# 403 이 아니라 404 — 그런 거래가 존재한다는 사실 자체도 알려주지 않는다.

def _shared_txn(session: Session, txn_id: int) -> Transaction:
    category = get_shared_category(session)
    txn = session.get(Transaction, txn_id)
    if category is None or txn is None or txn.category_id != category.id:
        raise HTTPException(404, "transaction not found")
    return txn


@router.get("/records", response_model=list[RecordRead])
def shared_records(
    tag_id: int | None = None,
    month: str | None = Query(None, description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> list[RecordRead]:
    category = get_shared_category(session)
    if category is None:
        return []
    return list_records(session, tag_id=tag_id, month=month, category_id=category.id)


@router.get("/tags", response_model=list[TagRead])
def shared_tags(session: Session = Depends(get_session)) -> list[Tag]:
    return list(session.exec(select(Tag).order_by(Tag.id)).all())


@router.post("/tags", response_model=TagRead, status_code=201)
def shared_create_tag(payload: TagCreate, session: Session = Depends(get_session)) -> Tag:
    obj = Tag(**payload.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.put("/transactions/{txn_id}/tags", response_model=list[TagRead])
def shared_set_tags(
    txn_id: int, payload: TransactionTagsSet, session: Session = Depends(get_session)
) -> list[Tag]:
    _shared_txn(session, txn_id)
    return replace_tags(session, txn_id, payload.tag_ids)


class SharedTxnPatch(SQLModel):
    """partner 가 고칠 수 있는 건 메모뿐. 금액·날짜·카테고리는 owner 몫이다."""

    memo: str | None = None


@router.patch("/transactions/{txn_id}")
def shared_update_txn(
    txn_id: int, payload: SharedTxnPatch, session: Session = Depends(get_session)
) -> dict:
    txn = _shared_txn(session, txn_id)
    if "memo" in payload.model_fields_set:
        txn.memo = payload.memo
    session.add(txn)
    session.commit()
    return {"id": txn.id, "memo": txn.memo}


@router.post("/transactions/{txn_id}/place", response_model=PlaceRead, status_code=201)
def shared_attach_place(
    txn_id: int, payload: PlaceCreate, session: Session = Depends(get_session)
) -> Place:
    """장소를 **새로 만들어** 붙인다. 기존 place_id 를 받지 않는 이유: 아무 번호나 넣어
    owner 의 개인 장소(이름·주소·좌표)를 공유 기록에 끌어올 수 있기 때문."""
    txn = _shared_txn(session, txn_id)
    place = create_place(session, payload.model_dump())
    txn.place_id = place.id
    session.add(txn)
    session.commit()
    return place


@router.get("/places/search")
def shared_search_places(q: str = Query(..., min_length=1)) -> list[dict]:
    """카카오 키워드 검색 프록시. 우리 DB 를 읽지 않으므로 partner 에게 열어도 된다."""
    return geocode.search_places(q)


@router.post("/photos", response_model=PhotoRead, status_code=201)
async def shared_upload_photo(
    file: UploadFile = File(...),
    transaction_id: int = Form(...),
    session: Session = Depends(get_session),
) -> Photo:
    _shared_txn(session, transaction_id)
    try:
        # SVG 제외 — 같은 출처에서 서빙되므로 스크립트가 든 파일을 남이 올리게 두지 않는다.
        return save_photo(
            session,
            filename=file.filename,
            data=await file.read(),
            transaction_id=transaction_id,
            allowed_ext=RASTER_EXT,
        )
    except PhotoRejected as e:
        raise HTTPException(e.status, e.detail) from e


# ---------- 내 정보 ----------

@router.get("/me")
def shared_me(member: Member = Depends(require_member)) -> dict:
    return {"id": member.id, "name": member.name, "color": member.color, "role": member.role.value}


class SharedMePatch(SQLModel):
    color: str


@router.patch("/me")
def shared_update_me(
    payload: SharedMePatch,
    member: Member = Depends(require_member),
    session: Session = Depends(get_session),
) -> dict:
    """본인 색만 바꿀 수 있다. 이름은 로그인 아이디라 여기서 바꾸지 않는다."""
    color = normalize_color(payload.color)
    if color is None:
        raise HTTPException(422, "색은 #RRGGBB 또는 색 이름(파랑·빨강 등)으로 주세요")
    row = session.get(Member, member.id)
    row.color = color
    session.add(row)
    session.commit()
    return {"id": row.id, "name": row.name, "color": row.color, "role": row.role.value}
