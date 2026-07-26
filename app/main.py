from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    accounts,
    budgets,
    categories,
    category_rules,
    net_worth,
    transactions,
)
from app.config import settings

app = FastAPI(title=settings.app_name)

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

for module in (accounts, categories, category_rules, transactions, budgets, net_worth):
    app.include_router(module.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
