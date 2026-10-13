"""공유 예산(데이트비용) 집계 테스트."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.services.shared_budget import compute_status, crosses_warning


def _spend(client: TestClient, account_id: int, category_id: int, amount: int,
           payer_id: int | None = None, when: str = "2026-10-05T19:00:00"):
    return client.post("/transactions", json={
        "account_id": account_id, "type": "expense", "amount": amount,
        "occurred_at": when, "category_id": category_id, "payer_id": payer_id,
    })


# ---------- 설정이 없을 때 ----------

def test_returns_none_without_shared_category(session: Session):
    assert compute_status(session, "2026-10") is None


def test_returns_none_when_month_has_no_budget(session: Session, date_budget):
    assert compute_status(session, "2026-11") is None  # 한도를 안 잡은 달


# ---------- 기본 계산 ----------

def test_computes_spent_remaining_usage(session: Session, client, account, date_budget):
    cat, limit = date_budget
    _spend(client, account.id, cat.id, 120_000)
    _spend(client, account.id, cat.id, 80_000)

    s = compute_status(session, "2026-10")

    assert s["limit"] == limit
    assert s["spent"] == 200_000
    assert s["remaining"] == 300_000
    assert s["usage_percent"] == 40.0


def test_other_month_spending_is_excluded(session: Session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 100_000, when="2026-10-05T19:00:00")
    _spend(client, account.id, cat.id, 400_000, when="2026-11-02T19:00:00")

    assert compute_status(session, "2026-10")["spent"] == 100_000


def test_non_shared_category_spending_is_excluded(
    session: Session, client, account, date_budget, make_category
):
    cat, _ = date_budget
    solo = make_category("내 점심")
    _spend(client, account.id, cat.id, 50_000)
    _spend(client, account.id, solo.id, 300_000)

    assert compute_status(session, "2026-10")["spent"] == 50_000


# ---------- 상태 전이 ----------

def test_state_is_ok_below_80_percent(session: Session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 100_000)  # 20%

    assert compute_status(session, "2026-10")["state"] == "ok"


def test_state_is_warning_at_80_percent(session: Session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 400_000)  # 정확히 80%

    assert compute_status(session, "2026-10")["state"] == "warning"


def test_state_is_over_at_100_percent(session: Session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 500_000)

    assert compute_status(session, "2026-10")["state"] == "over"


def test_overspending_shows_negative_remaining(session: Session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 620_000)

    s = compute_status(session, "2026-10")
    assert s["remaining"] == -120_000
    assert s["state"] == "over"


# ---------- 기여자 ----------




# ---------- 경고 임계 통과 ----------

def test_crosses_warning_only_on_first_crossing(session: Session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 410_000)  # 82%
    s = compute_status(session, "2026-10")

    assert crosses_warning(previous_spent=390_000, status=s) is True   # 78% -> 82%
    assert crosses_warning(previous_spent=405_000, status=s) is False  # 81% -> 82%, 이미 넘어있었음


# ---------- API ----------

def test_api_returns_status(client: TestClient, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 250_000)

    res = client.get("/shared/budget", params={"month": "2026-10"})

    assert res.status_code == 200
    assert res.json()["usage_percent"] == 50.0


def test_api_404_when_not_configured(client: TestClient):
    assert client.get("/shared/budget", params={"month": "2026-10"}).status_code == 404


# ---------- 사람 구분 없음 ----------

def test_status_has_no_per_person_breakdown(session: Session, client, account, date_budget, make_member):
    """누가 얼마 썼는지는 계산도 응답도 하지 않는다."""
    cat, _ = date_budget
    me = make_member("나", chat_id=111)
    _spend(client, account.id, cat.id, 70_000, payer_id=me.id)

    s = compute_status(session, "2026-10")

    assert "by_payer" not in s
    assert "나" not in str(s)


def test_shared_transactions_hide_payer_and_income(
    client, partner_client, account, date_budget, make_member
):
    cat, _ = date_budget
    me = make_member("나", chat_id=111)
    _spend(client, account.id, cat.id, 30_000, payer_id=me.id)
    client.post("/transactions", json={
        "account_id": account.id, "type": "income", "amount": 99_000,
        "occurred_at": "2026-10-06T12:00:00", "category_id": cat.id,
    })

    rows = partner_client.get("/shared/transactions?month=2026-10").json()

    assert [r["amount"] for r in rows] == [30_000]  # 수입은 빠진다
    assert all("payer_id" not in r for r in rows)
