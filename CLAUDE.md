# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TheRich is a personal (single-user) asset-management dashboard backend. Current scope is **Phase 1: net worth + spending (가계부)**. Stack: **FastAPI + SQLModel + Alembic**, SQLite for now (PostgreSQL later — keep schema/queries portable). A Next.js PWA frontend and a Telegram bot are planned but not in this repo yet.

Design rationale, roadmap, and product/UX decisions live in Claude's persistent memory (`therich-project`, `therich-features`, `therich-ai-cost`, `therich-design`, `user-devices`) — consult it for the "why" behind choices.

## Commands

```bash
# setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# migrations — run after ANY model change
alembic revision --autogenerate -m "<message>"   # generate migration
alembic upgrade head                              # apply (creates ./therich.db)

# run
uvicorn app.main:app --reload      # docs at http://127.0.0.1:8000/docs
```

- **No test suite yet.** Verification has been ad-hoc with `fastapi.testclient.TestClient` against `app.main:app`. (The `httpx2` deprecation warning it prints is harmless.)
- No linter/formatter configured.
- Settings (`DATABASE_URL`, `APP_NAME`) load from `.env` via `app/config.py`; both default sensibly, so `.env` is optional for local dev.

## Architecture

Layered — one responsibility per package:

- **`app/models/`** — SQLModel persistence.
  - `base.py`: `TimestampMixin` + **all enums** (`AccountType`, `AccountSide`, `TxnType`, `TxnSource`, `CategoryKind`, `MatchType`) — single source of truth.
  - `core.py`: finance tables — `account`, `category`, `category_rule`, `transaction`, `budget`, `net_worth_snapshot`.
  - `lifelog.py`: 맛집/추억 tables — `place`, `photo`, `tag`, `transaction_tag`.
  - `__init__.py` **imports every table** so `SQLModel.metadata` is fully populated — Alembic depends on this.
- **`app/schemas.py`** — API contracts (`*Create` / `*Read` / `*Update`). Routers use these; **table models are never exposed directly**.
- **`app/services/`** — domain logic (`classify.py` = category rule engine, `period.py` = month range helper).
- **`app/api/`** — one router module per resource, wired in `app/main.py`.
- **`alembic/`** — migrations. `env.py` sets the target to `SQLModel.metadata` and injects `DATABASE_URL` from `app.config.settings`; `script.py.mako` imports `sqlmodel`; `render_as_batch` is on for SQLite.

### The model ↔ schema pattern (spans files — read together)

Each entity is defined once as **`XxxBase(SQLModel)`** (shared editable fields) in `models/core.py`, then:
- table: `class Xxx(XxxBase, TimestampMixin, table=True)` — adds only the `id` PK.
- API: `XxxCreate(XxxBase)`, `XxxRead(XxxBase)` (+ `id`/timestamps), `XxxUpdate(SQLModel)` (all fields optional) in `schemas.py`.

To add/change an entity: edit the Base in `models/core.py` → mirror it in `schemas.py` → add/adjust the router → run the Alembic autogenerate + upgrade cycle. Because columns live on the Base, refactors that don't change columns produce **no migration**.

### Conventions & gotchas

- **Money is always an integer in the currency's smallest unit** (KRW = 원; USD would be cents). Never use float for money.
- **Transaction auto-classification**: `POST /transactions` with no `category_id` calls `services/classify.py`, which applies `category_rule` rows (priority desc; `contains`/`exact`/`regex`) to fill the category. LLM classification is only a planned fallback for what rules miss — don't reach for AI where a rule suffices.
- **Route ordering**: static sub-paths must be declared before `/{id}` int routes — e.g. `GET /budgets/status` comes before `GET /budgets/{budget_id}`.
- `net_worth_snapshot` and the `place`/`photo`/`tag`/`transaction_tag` tables exist but have **no routers yet**.

## Domain context files

- `README.md` — quick start.
- `토스증권-OpenAPI-기초정리.md` — Toss Securities Open API primer for the Phase 2 integration. Key constraints to remember: the Toss Open API is **REST-only (no websocket; poll ≤ 1s)** and exposes only 6 categories (auth/market-data/stock-info/market-info/account/order) — **no news or disclosure endpoints**.
- `혜택_청약_정리.md` — **contains the user's personal profile** (birth year, address, family, housing/subscription-account status), used for the future benefit/청약/policy-matching feature. Treat as sensitive: reference it for domain logic, but do not copy personal details into code, logs, or outputs.
