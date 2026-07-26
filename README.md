# TheRich

개인 자산관리 대시보드 백엔드 — **Phase 1 (순자산 + 지출)**.
스택: **FastAPI + SQLModel + Alembic** (초기 DB는 SQLite, 나중에 PostgreSQL).

## 빠른 시작

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# DB 마이그레이션 (최초 1회 + 스키마 바뀔 때마다)
alembic revision --autogenerate -m "init schema"   # 마이그레이션 파일 생성
alembic upgrade head                                # 적용 → therich.db 생성
python -m app.seed                                  # 기본 카테고리·분류규칙 시드 (선택)

# 서버 실행
uvicorn app.main:app --reload
```

- API 문서(Swagger): http://127.0.0.1:8000/docs
- 헬스체크: http://127.0.0.1:8000/health

## 프론트엔드 (웹 PWA)

`web/` 에 Next.js 앱 — 별도 실행:

```bash
cd web && pnpm install && pnpm dev   # http://localhost:3000
```

## 텔레그램 봇 (모바일 지출 입력)

봇은 **별도 프로세스**로, 텍스트 지출을 백엔드 API로 저장한다.

```bash
# 1) 텔레그램에서 @BotFather 대화 → /newbot → 봇 토큰 발급
# 2) 발급 토큰을 .env 에 넣기 (.env.example 참고)
#    TELEGRAM_BOT_TOKEN=<발급받은 토큰>
# 3) 백엔드가 켜져 있어야 함 (uvicorn app.main:app)
python -m app.telegram_bot
# 4) 봇에게 /chatid 를 보내 나온 id 를 .env 의 TELEGRAM_CHAT_ID 에 넣으면
#    매일 00:30(KST) 지출 넛지를 받음
```

- 사용: `스타벅스 5500` 처럼 '가맹점 금액'을 보내면 확인 후 저장(규칙엔진 자동분류).
- `/month` 이번 달 요약, `/chatid` chat id 확인.
- 사진 OCR 은 아직 스텁(텍스트 입력만) — 로컬 OCR 은 후속.
- **토큰은 개인 자격증명**이라 저장소에 커밋 금지(`.env` 는 gitignore).

## 구조

```
app/
  config.py        설정(pydantic-settings, .env)
  db.py            엔진 · 세션
  main.py          FastAPI 앱
  models/
    base.py        공통 믹스인 + Enum
    core.py        account · category · category_rule · transaction · budget · net_worth_snapshot
    lifelog.py     place · photo · tag · transaction_tag (맛집/추억 기록)
  api/
    accounts.py    샘플 라우터 (스택 검증용)
alembic/           DB 마이그레이션
```

## 메모
- 금액은 **최소단위 정수**(원)로 저장 — float 금지.
- 라우터: accounts · categories · category-rules · transactions · budgets · net-worth · tags · places · photos · records.
- 순자산 자동 스냅샷: `app/scheduler.py`(APScheduler) — 매월 말일 + 시작 보정.
- 자세한 설계 배경은 `~/.claude/.../memory` 의 `therich-*` 메모 참조.
