"""데모 생성기. 실제 DB 를 절대 건드리지 않는다는 점과, 만든 데모가 쓸 만한지를 본다."""

import hashlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from app.demo import _guard, _recent_months

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("db, uploads", [
    ("therich.db", "uploads-demo"),      # 실제 DB
    ("mydata.db", "uploads-demo"),       # 이름에 demo 없음
    ("therich-demo.db", "uploads"),      # 실제 사진 폴더
    ("therich-demo.sqlite", "uploads-demo"),
])
def test_guard_refuses_anything_that_could_be_real_data(db, uploads):
    with pytest.raises(SystemExit):
        _guard(Path(db), Path(uploads))


def test_guard_allows_demo_paths():
    _guard(Path("therich-demo.db"), Path("uploads-demo"))  # 예외 없으면 통과


def test_recent_months_cross_year_boundary():
    from datetime import date

    assert _recent_months(date(2026, 2, 10), 4) == [(2025, 11), (2025, 12), (2026, 1), (2026, 2)]


def _md5(p: Path) -> str | None:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else None


def test_demo_builds_an_isolated_db(tmp_path):
    """실제 생성기를 끝까지 돌린다. 데이터가 고르게 들어가고 실제 DB·사진은 그대로여야 한다."""
    real_db, real_uploads = ROOT / "therich.db", ROOT / "uploads"
    before_db = _md5(real_db)
    before_uploads = sorted(os.listdir(real_uploads)) if real_uploads.exists() else []

    db, uploads = tmp_path / "t-demo.db", tmp_path / "uploads-demo"
    env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "UPLOAD_DIR")}
    res = subprocess.run(
        [sys.executable, "-m", "app.demo", "--db", str(db), "--uploads", str(uploads), "--password", "demo-test-pw"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert res.returncode == 0, res.stderr[-2000:]

    assert _md5(real_db) == before_db, "실제 DB 가 바뀌었다"
    after_uploads = sorted(os.listdir(real_uploads)) if real_uploads.exists() else []
    assert after_uploads == before_uploads, "실제 uploads/ 가 바뀌었다"

    con = sqlite3.connect(db)
    q = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
    assert q("SELECT count(*) FROM member WHERE name='demo' AND role='owner'") == 1
    assert q("SELECT count(*) FROM member WHERE name='demo-partner' AND role='partner'") == 1
    assert q("SELECT count(*) FROM category WHERE is_shared=1") == 1
    assert q('SELECT count(*) FROM "transaction"') > 150
    assert q("SELECT count(*) FROM photo") > 10
    assert len(list(uploads.iterdir())) == q("SELECT count(*) FROM photo")
    # 개인정보 규칙: 데모에 비밀번호 원문이 남지 않는다
    assert "demo-test-pw" not in db.read_bytes().decode("latin-1")
