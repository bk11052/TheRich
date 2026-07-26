from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import (
    accounts,
    budgets,
    cards,
    categories,
    category_rules,
    net_worth,
    photos,
    places,
    records,
    tags,
    transactions,
)
from app.config import settings
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 순자산 자동 스냅샷 스케줄러 시작 (백엔드 실행 중에만 동작)
    scheduler = start_scheduler()
    app.state.scheduler = scheduler
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# 로컬 개발용 CORS: Next.js dev 서버(3000)에서 API 호출 허용.
# 단일 사용자 로컬 앱이라 우선 localhost 계열을 폭넓게 허용.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    accounts,
    categories,
    category_rules,
    transactions,
    budgets,
    net_worth,
    tags,
    places,
    photos,
    records,
    cards,
):
    app.include_router(module.router)

# 업로드된 사진 정적 서빙 (/uploads/<파일명>)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
