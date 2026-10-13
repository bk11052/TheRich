"""인증·권한. 이 파일이 깨지면 자산이 새는 것이므로 가장 중요하다."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import SESSION_COOKIE

from .conftest import OWNER_PASSWORD

# owner 전용이어야 하는 경로. 하나라도 빠지면 partner 에게 열린다.
OWNER_ONLY_GET = [
    "/accounts",
    "/categories",
    "/category-rules",
    "/transactions",
    "/budgets",
    "/net-worth/current",
    "/members",
    "/tags",
    "/places",
    "/cards",
    "/records",
]
SHARED_GET = ["/shared/budget?month=2026-10", "/shared/members", "/shared/transactions?month=2026-10"]


# ---------- 로그인 ----------

def test_login_sets_session_cookie(anon_client: TestClient, owner):
    res = anon_client.post(
        "/auth/login", json={"name": owner.name, "password": OWNER_PASSWORD}
    )

    assert res.status_code == 200
    assert SESSION_COOKIE in anon_client.cookies


def test_login_rejects_wrong_password(anon_client: TestClient, owner):
    res = anon_client.post("/auth/login", json={"name": owner.name, "password": "틀림"})

    assert res.status_code == 401
    assert SESSION_COOKIE not in anon_client.cookies


def test_unknown_name_and_wrong_password_give_the_same_error(
    anon_client: TestClient, owner
):
    """계정 이름이 존재하는지 떠볼 수 없어야 한다."""
    missing = anon_client.post("/auth/login", json={"name": "없는사람", "password": "x"})
    wrong = anon_client.post("/auth/login", json={"name": owner.name, "password": "x"})

    assert missing.status_code == wrong.status_code == 401
    assert missing.json()["detail"] == wrong.json()["detail"]


def test_member_without_password_cannot_log_in(anon_client: TestClient, make_member):
    """비밀번호 미설정 멤버(텔레그램만 쓰는 사람)는 로그인 대상이 아니다."""
    make_member("비번없음")

    res = anon_client.post("/auth/login", json={"name": "비번없음", "password": ""})

    assert res.status_code == 401


def test_inactive_member_cannot_log_in(anon_client: TestClient, session, partner):
    partner.active = False
    session.add(partner)
    session.commit()

    from .conftest import PARTNER_PASSWORD

    res = anon_client.post(
        "/auth/login", json={"name": partner.name, "password": PARTNER_PASSWORD}
    )

    assert res.status_code == 401


# ---------- 미인증 차단 ----------

@pytest.mark.parametrize("path", OWNER_ONLY_GET + SHARED_GET)
def test_anonymous_is_rejected_everywhere(anon_client: TestClient, path):
    assert anon_client.get(path).status_code == 401


def _probe_paths() -> list[str]:
    """OpenAPI 에 선언된 GET 경로 전체. 경로 파라미터는 더미 id 로 채운다."""
    import re

    exempt = {"/health", "/auth/login", "/auth/status"}
    out = []
    for path, ops in app.openapi()["paths"].items():
        if path in exempt or "get" not in ops:
            continue
        out.append(re.sub(r"\{[^}]+\}", "1", path))
    return sorted(set(out))


@pytest.mark.parametrize("path", _probe_paths())
def test_no_get_route_is_readable_without_login(anon_client: TestClient, path):
    """OpenAPI 에서 경로를 직접 읽어오므로, 새 라우터를 인증 없이 추가하면 여기서 깨진다."""
    res = anon_client.get(path)

    assert res.status_code == 401, f"{path} 가 미인증에 {res.status_code} 로 응답했다"


# ---------- partner 차단 ----------

@pytest.mark.parametrize("path", OWNER_ONLY_GET)
def test_partner_is_forbidden_on_owner_routes(partner_client: TestClient, path):
    assert partner_client.get(path).status_code == 403


@pytest.mark.parametrize("path", SHARED_GET)
def test_partner_can_read_shared_routes(partner_client: TestClient, path):
    # 공유 예산 미설정이면 404 지만, 403/401 만 아니면 권한은 통과한 것.
    assert partner_client.get(path).status_code in (200, 404)


def test_partner_cannot_write_transactions(partner_client: TestClient):
    res = partner_client.post("/transactions", json={
        "account_id": 1, "type": "expense", "amount": 1000,
        "occurred_at": "2026-10-01T12:00:00",
    })

    assert res.status_code == 403


# ---------- owner 허용 ----------

@pytest.mark.parametrize("path", OWNER_ONLY_GET)
def test_owner_can_read_everything(client: TestClient, path):
    assert client.get(path).status_code == 200


# ---------- 정보 유출 ----------

def test_member_responses_never_include_password_hash(client: TestClient):
    body = client.get("/members").text

    assert "password_hash" not in body
    assert "scrypt$" not in body


def test_shared_members_hides_chat_id_and_role(partner_client: TestClient, make_member):
    make_member("상대", chat_id=999)

    rows = partner_client.get("/shared/members").json()

    assert rows, "멤버가 보여야 한다"
    for row in rows:
        assert set(row) == {"id", "name", "color"}


def test_shared_transactions_exclude_personal_spending(
    client: TestClient, partner_client: TestClient, account, make_category, date_budget
):
    cat, _ = date_budget
    personal = make_category("내 개인지출")
    for category_id, merchant in ((cat.id, "데이트"), (personal.id, "개인")):
        client.post("/transactions", json={
            "account_id": account.id, "type": "expense", "amount": 10_000,
            "occurred_at": "2026-10-05T12:00:00", "category_id": category_id,
            "merchant": merchant,
        })

    merchants = [t["merchant"] for t in
                 partner_client.get("/shared/transactions?month=2026-10").json()]

    assert merchants == ["데이트"]


# ---------- 세션 수명 ----------

def test_logout_revokes_the_session_on_the_server(client: TestClient):
    """쿠키만 지우면 토큰이 살아있다. 서버 행도 지워야 한다."""
    token = client.cookies[SESSION_COOKIE]
    client.post("/auth/logout")

    client.cookies.set(SESSION_COOKIE, token)  # 탈취한 토큰을 다시 들이민 상황
    assert client.get("/accounts").status_code == 401


def test_expired_session_is_rejected(anon_client: TestClient, session, owner):
    from datetime import datetime, timedelta

    from sqlmodel import select

    from app.models.core import Session as SessionRow

    anon_client.post("/auth/login", json={"name": owner.name, "password": OWNER_PASSWORD})
    row = session.exec(select(SessionRow)).first()
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    session.add(row)
    session.commit()

    assert anon_client.get("/accounts").status_code == 401


def test_me_returns_the_logged_in_member(client: TestClient, owner):
    assert client.get("/auth/me").json()["name"] == owner.name


def test_status_is_public_and_reports_anonymous(anon_client: TestClient):
    res = anon_client.get("/auth/status")

    assert res.status_code == 200
    assert res.json()["authenticated"] is False


# ---------- 서비스 토큰 (텔레그램 봇) ----------

@pytest.fixture
def service_token(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "service_token", "svc-test-token")
    return "svc-test-token"


def test_service_token_grants_owner_access(anon_client: TestClient, owner, service_token):
    res = anon_client.get(
        "/accounts", headers={"Authorization": f"Bearer {service_token}"}
    )

    assert res.status_code == 200


def test_wrong_service_token_is_rejected(anon_client: TestClient, owner, service_token):
    res = anon_client.get("/accounts", headers={"Authorization": "Bearer nope"})

    assert res.status_code == 401


def test_service_token_without_any_owner_is_rejected(
    anon_client: TestClient, service_token
):
    """owner 가 없으면 토큰이 맞아도 대신할 사람이 없으므로 거절."""
    res = anon_client.get(
        "/accounts", headers={"Authorization": f"Bearer {service_token}"}
    )

    assert res.status_code == 401


def test_unset_service_token_never_matches(anon_client: TestClient, owner, monkeypatch):
    """SERVICE_TOKEN 미설정일 때 빈 Bearer 로 뚫리면 안 된다."""
    from app.config import settings

    monkeypatch.setattr(settings, "service_token", None)
    for header in ("Bearer ", "Bearer None", "Bearer"):
        res = anon_client.get("/accounts", headers={"Authorization": header})
        assert res.status_code == 401, header


# ---------- 로그인 실패 제한 ----------

def _fail(client: TestClient, name: str, n: int):
    for _ in range(n):
        client.post("/auth/login", json={"name": name, "password": "wrong"})


def test_login_locks_after_repeated_failures(anon_client: TestClient, owner):
    from app.services.login_throttle import MAX_FAILURES

    _fail(anon_client, owner.name, MAX_FAILURES)

    # 잠긴 뒤에는 맞는 비밀번호도 막혀야 한다 — 아니면 잠금이 의미가 없다.
    res = anon_client.post("/auth/login", json={"name": owner.name, "password": OWNER_PASSWORD})
    assert res.status_code == 429
    assert int(res.headers["Retry-After"]) > 0


def test_fewer_failures_than_limit_do_not_lock(anon_client: TestClient, owner):
    from app.services.login_throttle import MAX_FAILURES

    _fail(anon_client, owner.name, MAX_FAILURES - 1)

    res = anon_client.post("/auth/login", json={"name": owner.name, "password": OWNER_PASSWORD})
    assert res.status_code == 200


def test_success_resets_the_failure_count(anon_client: TestClient, owner):
    from app.services.login_throttle import MAX_FAILURES

    _fail(anon_client, owner.name, MAX_FAILURES - 1)
    anon_client.post("/auth/login", json={"name": owner.name, "password": OWNER_PASSWORD})
    _fail(anon_client, owner.name, MAX_FAILURES - 1)

    res = anon_client.post("/auth/login", json={"name": owner.name, "password": OWNER_PASSWORD})
    assert res.status_code == 200


def test_unknown_names_are_throttled_too(anon_client: TestClient):
    """없는 이름만 안 잠기면 '잠기는 이름 = 실제 계정'이 되어 계정을 떠볼 수 있다."""
    from app.services.login_throttle import MAX_FAILURES

    _fail(anon_client, "없는사람", MAX_FAILURES)

    res = anon_client.post("/auth/login", json={"name": "없는사람", "password": "x"})
    assert res.status_code == 429


def test_lock_is_per_name_so_others_are_unaffected(anon_client: TestClient, owner, partner):
    from app.services.login_throttle import MAX_FAILURES

    from .conftest import PARTNER_PASSWORD

    _fail(anon_client, owner.name, MAX_FAILURES)

    res = anon_client.post("/auth/login", json={"name": partner.name, "password": PARTNER_PASSWORD})
    assert res.status_code == 200


def test_lock_expires():
    from app.services import login_throttle as t

    for i in range(t.MAX_FAILURES):
        t.record_failure("1.2.3.4", "주인", now=1000.0 + i)
    assert t.seconds_locked("1.2.3.4", "주인", now=1010.0) > 0
    assert t.seconds_locked("1.2.3.4", "주인", now=1010.0 + t.LOCK_SECONDS) == 0
