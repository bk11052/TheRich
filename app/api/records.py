"""기록(라이프로그) = 사진·장소·태그로 보강된 거래 조회. owner 는 전체를 본다."""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.deps import require_owner
from app.schemas import RecordRead
from app.services.lifelog import list_records as build_records

router = APIRouter(prefix="/records", tags=["records"], dependencies=[Depends(require_owner)])


@router.get("", response_model=list[RecordRead])
def list_records(
    tag_id: int | None = None,
    month: str | None = Query(None, description="YYYY-MM"),
    session: Session = Depends(get_session),
) -> list[RecordRead]:
    """사진/장소/태그 중 하나라도 있는 거래를 최신순으로."""
    return build_records(session, tag_id=tag_id, month=month)
