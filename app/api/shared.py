"""공유 예산(데이트비용) 현황 조회."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db import get_session
from app.services.shared_budget import compute_status

router = APIRouter(prefix="/shared", tags=["shared"])


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
