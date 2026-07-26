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
- 스켈레톤이라 `accounts` 라우터가 테이블 모델을 그대로 입출력에 씀 → 다음 단계에서 Create/Read 스키마 분리 예정.
- 자세한 설계 배경은 `~/.claude/.../memory` 의 `therich-*` 메모 참조.
