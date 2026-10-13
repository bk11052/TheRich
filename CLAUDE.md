# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TheRich is a personal asset-management dashboard backend. It is **single-user for everything except one shared budget**: the owner and one partner log 데이트비용 to a common monthly limit (see *Shared budget* below). Everything else — net worth, portfolio, other spending — stays private to the owner. Current scope is **Phase 1: net worth + spending (가계부)**. Stack: **FastAPI + SQLModel + Alembic**, SQLite for now (PostgreSQL later — keep schema/queries portable). A Next.js PWA frontend and a Telegram bot are planned but not in this repo yet.

Design rationale, roadmap, and product/UX decisions live in Claude's persistent memory (`therich-project`, `therich-features`, `therich-ai-cost`, `therich-design`, `user-devices`) — consult it for the "why" behind choices.

## Security & privacy (hard rule)

**Never commit secrets or personal data to this repository.** It is intended to be pushable to a remote at any time, so "it's only local" is not a safeguard — anything in git history ships the moment a remote is added.

**Never tracked, no exceptions:**

- Credentials of any kind — API keys, tokens, client secrets, passwords, cookies, private keys. Includes `TELEGRAM_BOT_TOKEN`, `KAKAO_REST_API_KEY`, `NEXT_PUBLIC_KAKAO_JS_KEY`, `TOSS_CLIENT_ID` / `TOSS_CLIENT_SECRET`. These live in `.env` / `web/.env.local` only; `.env.example` carries **empty placeholders and comments, never real values**.
- The user's personal data — real name, resident registration number, address, phone, email, date of birth, family composition, military service, school/employer, salary, account/card numbers, balances, holdings, transactions, benefit/청약 eligibility details.
- Real data files — `*.db`, `*.sqlite`, `uploads/` (receipt/food photos), CSV exports, screenshots of bank or brokerage apps.

**Consequences for how code is written:**

- Seed and demo data must be synthetic (`app/seed_demo.py`). Never seed the repo with the user's real accounts, balances, or transactions.
- Never write personal data into source, comments, commit messages, logs, test fixtures, or error strings. When domain logic needs the user's profile, read it at runtime from an ignored file or the DB — do not inline it.
- Personal profile/benefit notes stay **untracked** (`.gitignore`d) and are referenced for domain logic only. `혜택_청약_정리.md` is such a file: it exists locally, is ignored by git, and was purged from history on 2026-09-26.
- Design rationale belongs in Claude's memory (outside the repo), not in tracked docs, when it would require quoting personal data.

**The audit runs automatically.** `.githooks/pre-push` invokes `scripts/audit-secrets.sh` on every push and aborts if anything is found. It is tracked, so a fresh clone needs the hook path enabled once:

```bash
git config core.hooksPath .githooks
```

Run `./scripts/audit-secrets.sh` by hand any time. `git push --no-verify` bypasses the hook — only for confirmed false positives. If a leak is already committed, purging history is not enough once a remote exists: **rotate the credential first**, then rewrite history.

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

- **Tests**: `pytest` (see `requirements-dev.txt`). `tests/conftest.py` gives each test a fresh in-memory SQLite through `dependency_overrides`, plus `anon_client` / `client` (owner) / `partner_client` fixtures.
- No linter/formatter configured.
- Settings (`DATABASE_URL`, `APP_NAME`) load from `.env` via `app/config.py`; both default sensibly, so `.env` is optional for local dev.

## Architecture

Layered — one responsibility per package:

- **`app/models/`** — SQLModel persistence.
  - `base.py`: `TimestampMixin` + **all enums** (`AccountType`, `AccountSide`, `TxnType`, `TxnSource`, `CategoryKind`, `MatchType`) — single source of truth.
  - `core.py`: finance tables — `member`, `account`, `category`, `category_rule`, `transaction`, `budget`, `net_worth_snapshot`.
  - `lifelog.py`: 맛집/추억 tables — `place`, `photo`, `tag`, `transaction_tag`.
  - `__init__.py` **imports every table** so `SQLModel.metadata` is fully populated — Alembic depends on this.
- **`app/schemas.py`** — API contracts (`*Create` / `*Read` / `*Update`). Routers use these; **table models are never exposed directly**.
- **`app/services/`** — domain logic (`classify.py` = category rule engine, `shared_budget.py` = 데이트비용 aggregation, `lifelog.py` = records/photos/places/tags shared by owner and `/shared` routes, `period.py` = month range helper).
- **`app/api/`** — one router module per resource, wired in `app/main.py`.
- **`alembic/`** — migrations. `env.py` sets the target to `SQLModel.metadata` and injects `DATABASE_URL` from `app.config.settings`; `script.py.mako` imports `sqlmodel`; `render_as_batch` is on for SQLite.

### The model ↔ schema pattern (spans files — read together)

Each entity is defined once as **`XxxBase(SQLModel)`** (shared editable fields) in `models/core.py`, then:
- table: `class Xxx(XxxBase, TimestampMixin, table=True)` — adds only the `id` PK.
- API: `XxxCreate(XxxBase)`, `XxxRead(XxxBase)` (+ `id`/timestamps), `XxxUpdate(SQLModel)` (all fields optional) in `schemas.py`.

To add/change an entity: edit the Base in `models/core.py` → mirror it in `schemas.py` → add/adjust the router → run the Alembic autogenerate + upgrade cycle. Because columns live on the Base, refactors that don't change columns produce **no migration**.

### Shared budget (데이트비용)

Two people log to one monthly limit. The model reuses what already existed instead of adding a parallel budget system:

- `Category.is_shared=True` marks the shared category. Its `Budget` row for a month **is** the shared limit, so `/budgets` and `/budgets/status` keep working unchanged.
- `Member` maps a person to a `telegram_chat_id`. The bot accepts input **only from registered chat_ids** — a Telegram bot answers anyone who finds its username, so without this anybody could write to the ledger.
- `Transaction.payer_id` records who actually paid. Contributions are shown per person but **no settlement (1/N) is computed** — that was an explicit product decision.
- `services/shared_budget.py` derives state: `ok` / `warning` (>= `WARN_RATIO`, 0.8) / `over` (>= 1.0). `crosses_warning()` exists so the bot warns on the *first* crossing only rather than on every later expense.

### Alembic on SQLite — two traps hit in practice

Both come from SQLite lacking real `ALTER TABLE`, so `render_as_batch` rebuilds the table:

1. **A new `NOT NULL` column needs `server_default`** when the table already has rows, or you get `Cannot add a NOT NULL column with default value NULL`. Add `server_default=sa.false()` (etc.) in the migration; the model default still governs new inserts.
2. **Batch mode rejects unnamed constraints** — autogenerate emits `create_foreign_key(None, ...)`, which raises `Constraint must have a name`. Name it explicitly, and use the same name in `downgrade`.

A migration that fails midway can leave `member`-style partial tables and `_alembic_tmp_<table>` behind while `alembic_version` stays on the old revision. Drop those leftovers before retrying, and verify the fix with a **down-then-up round trip on a copy of the DB**, not on `therich.db`.

### Authentication and roles

The API was fully open until the partner needed dashboard access. Hiding tabs in the
frontend would have been meaningless — anyone who can load the page can also request
`/accounts` directly — so the split is enforced server-side.

- **`Member.role`** is `owner` or `partner`. `owner` reaches everything; `partner`
  reaches **only `/shared/*`**.
- **The 데이트비용 and 기록 tabs are the same screen for both people.** Both read and write
  through `/shared/*` (the owner is allowed there too), so they see identical data with
  identical scope: records attached to shared-category transactions only. The owner-only
  `/records`, `/photos`, `/places`, `/tags` routes still exist and are tested but the web
  app no longer calls them. 더보기 differs by role: the partner sees only her own colour.
- **What `/shared` deliberately withholds**: any transaction outside the shared category
  (404, not 403); existing place ids (a partner can only create-and-attach, or she could
  enumerate the owner's private places onto a shared record); tags used only on personal
  transactions (tag names alone can be private); SVG uploads (served from the API origin,
  so script inside could call the API with the owner's session).
- **Default is deny.** Every router carries `dependencies=[Depends(require_owner)]`;
  `/shared` lowers it to `require_member` and `/auth` is open. A router added without
  thinking is therefore owner-only, not public. `tests/test_auth.py` reads the OpenAPI
  schema and probes every GET route anonymously, so a route that forgets auth fails.
- **Sessions**: a random token in an httpOnly cookie; the DB stores only its SHA-256
  hash, so a leaked database cannot be replayed as a login. Logout deletes the row,
  not just the cookie.
- **Passwords**: stdlib `hashlib.scrypt`, serialised as `scrypt$n$r$p$salt$hash` so the
  parameters travel with the value. `password_hash` is `exclude=True` on the model and
  absent from `MemberRead`, so it cannot leak through the API.
- **Non-human clients** (the Telegram bot) send `Authorization: Bearer $SERVICE_TOKEN`
  and resolve to the owner. The token lives in `.env`.
- `/shared/members` returns only `id`/`name`/`color` — a partner has no reason to see
  anyone's `telegram_chat_id` or role.

Accounts are managed from the CLI, never over HTTP, and passwords are prompted rather
than passed as arguments so they stay out of shell history:

```bash
python -m app.manage list
python -m app.manage set-password <name>
python -m app.manage add-partner <name>
```

### Conventions & gotchas

- **Money is always an integer in the currency's smallest unit** (KRW = 원; USD would be cents). Never use float for money.
- **Transaction auto-classification**: `POST /transactions` with no `category_id` calls `services/classify.py`, which applies `category_rule` rows (priority desc; `contains`/`exact`/`regex`) to fill the category. LLM classification is only a planned fallback for what rules miss — don't reach for AI where a rule suffices.
- **Route ordering**: static sub-paths must be declared before `/{id}` int routes — e.g. `GET /budgets/status` comes before `GET /budgets/{budget_id}`.
- `net_worth_snapshot` and the `place`/`photo`/`tag`/`transaction_tag` tables exist but have **no routers yet**.

## Domain context files

- `README.md` — quick start.
- `토스증권-OpenAPI-기초정리.md` — Toss Securities Open API primer for the Phase 2 integration. Key constraints to remember: the Toss Open API is **REST-only (no websocket; poll ≤ 1s)** and exposes only 6 categories (auth/market-data/stock-info/market-info/account/order) — **no news or disclosure endpoints**.
- `혜택_청약_정리.md` — **untracked / git-ignored** (see Security & privacy). Local-only notes holding the maintainer's profile and benefit/청약 eligibility, used as domain input for the future policy-matching feature. Present in the working tree only. Reference it for domain logic; never copy its contents into code, logs, commit messages, or outputs, and never re-add it to git.
