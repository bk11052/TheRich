from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models.core import NetWorthSnapshot
from app.schemas import (
    NetWorthCurrent,
    NetWorthSnapshotCreate,
    NetWorthSnapshotRead,
)
from app.services.networth import capture_snapshot, compute_current

router = APIRouter(prefix="/net-worth", tags=["net-worth"])


@router.get("/current", response_model=NetWorthCurrent)
def current_net_worth(session: Session = Depends(get_session)) -> dict:
    """활성 계좌 잔액에서 실시간 계산한 현재 순자산 + 자산배분."""
    return compute_current(session)


@router.get("/snapshots", response_model=list[NetWorthSnapshotRead])
def list_snapshots(
    limit: int = Query(24, le=120),
    session: Session = Depends(get_session),
) -> list[NetWorthSnapshot]:
    """순자산 추이용 스냅샷 (날짜 오름차순)."""
    rows = session.exec(
        select(NetWorthSnapshot)
        .order_by(NetWorthSnapshot.snapshot_date.desc())
        .limit(limit)
    ).all()
    return list(reversed(rows))


@router.post("/snapshots", response_model=NetWorthSnapshotRead, status_code=201)
def create_snapshot(
    payload: NetWorthSnapshotCreate | None = None,
    session: Session = Depends(get_session),
) -> NetWorthSnapshot:
    """현재 순자산을 스냅샷으로 저장 (같은 날짜면 갱신). 합계는 서버가 계좌에서 계산."""
    snapshot_date = (payload.snapshot_date if payload else None) or date.today()
    return capture_snapshot(session, snapshot_date)


@router.delete("/snapshots/{snapshot_id}", status_code=204)
def delete_snapshot(
    snapshot_id: int, session: Session = Depends(get_session)
) -> None:
    obj = session.get(NetWorthSnapshot, snapshot_id)
    if not obj:
        raise HTTPException(404, "snapshot not found")
    session.delete(obj)
    session.commit()
