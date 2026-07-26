"""백그라운드 예약 작업 (APScheduler).

현재: 순자산 월말 자동 스냅샷.
- 매월 말일 23:59 → 현재 순자산을 스냅샷으로 저장(월말 날짜, upsert).
- 서버 시작 시 이번 달 스냅샷이 없으면 즉시 보정 캡처(비-24/7 환경 대비).

백엔드(uvicorn) 프로세스 안에서 도므로, 서버가 꺼진 시각의 회차는 건너뛴다.
텔레그램 넛지·아침 브리핑 등 향후 예약 작업도 이 스케줄러에 add_job 하면 된다.
"""

from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session

from app.db import engine
from app.services.networth import capture_snapshot, ensure_month_snapshot, month_end


def _capture_month_end() -> None:
    with Session(engine) as session:
        snap = capture_snapshot(session, month_end(date.today()))
        print(f"[scheduler] 순자산 스냅샷 저장: {snap.snapshot_date} = {snap.net_worth}")


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    # 매월 말일 23:59 (서버 로컬시간)
    scheduler.add_job(
        _capture_month_end,
        CronTrigger(day="last", hour=23, minute=59),
        id="monthly_networth_snapshot",
        replace_existing=True,
    )
    scheduler.start()

    # 시작 보정: 이번 달 스냅샷 없으면 즉시 캡처
    with Session(engine) as session:
        if ensure_month_snapshot(session):
            print("[scheduler] 이번 달 순자산 스냅샷 없음 → 보정 캡처 완료")

    job = scheduler.get_job("monthly_networth_snapshot")
    if job:
        print(f"[scheduler] 시작됨. 다음 순자산 스냅샷: {job.next_run_time}")
    return scheduler
