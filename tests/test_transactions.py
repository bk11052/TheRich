"""POST/GET /transactions 통합 테스트.

라우터 → 규칙엔진 → DB 까지 실제로 통과시켜, 계층이 제대로 엮였는지 본다.
"""

from fastapi.testclient import TestClient

from app.models.base import MatchType


def _payload(account_id: int, **over) -> dict:
    base = {
        "account_id": account_id,
        "type": "expense",
        "amount": 4500,
        "occurred_at": "2026-07-26T09:00:00",
        "merchant": "스타벅스 강남R점",
    }
    base.update(over)
    return base


def test_create_transaction_returns_201_and_id(client: TestClient, account):
    res = client.post("/transactions", json=_payload(account.id))

    assert res.status_code == 201
    body = res.json()
    assert body["id"] > 0
    assert body["amount"] == 4500
    assert body["account_id"] == account.id


def test_create_transaction_autoclassifies_from_rule(
    client: TestClient, account, make_category, make_rule
):
    """category_id 를 안 보내면 규칙엔진이 채워야 한다 — 이 앱의 간판 기능."""
    cafe = make_category("카페/간식")
    make_rule("스타벅스", cafe.id, MatchType.contains)

    res = client.post("/transactions", json=_payload(account.id))

    assert res.status_code == 201
    assert res.json()["category_id"] == cafe.id


def test_explicit_category_is_not_overwritten_by_rule(
    client: TestClient, account, make_category, make_rule
):
    """사용자가 직접 고른 카테고리를 규칙엔진이 덮어쓰면 안 된다."""
    cafe = make_category("카페/간식")
    chosen = make_category("접대비")
    make_rule("스타벅스", cafe.id, MatchType.contains)

    res = client.post(
        "/transactions", json=_payload(account.id, category_id=chosen.id)
    )

    assert res.json()["category_id"] == chosen.id


def test_create_transaction_without_matching_rule_leaves_category_null(
    client: TestClient, account
):
    res = client.post("/transactions", json=_payload(account.id, merchant="듣보잡가게"))

    assert res.status_code == 201
    assert res.json()["category_id"] is None


def test_create_transaction_rejects_invalid_amount(client: TestClient, account):
    """amount 에 문자열을 넣으면 함수까지 가지도 않고 422 로 걸러져야 한다."""
    res = client.post("/transactions", json=_payload(account.id, amount="사천오백"))

    assert res.status_code == 422


def test_get_missing_transaction_returns_404(client: TestClient):
    assert client.get("/transactions/99999").status_code == 404


def test_list_transactions_filters_by_month(client: TestClient, account):
    client.post("/transactions", json=_payload(account.id, occurred_at="2026-07-10T12:00:00"))
    client.post("/transactions", json=_payload(account.id, occurred_at="2026-08-10T12:00:00"))

    july = client.get("/transactions", params={"month": "2026-07"}).json()
    august = client.get("/transactions", params={"month": "2026-08"}).json()

    assert len(july) == 1
    assert len(august) == 1
    assert july[0]["occurred_at"].startswith("2026-07")


def test_list_transactions_filters_by_account(client: TestClient, account, session):
    from app.models.base import AccountSide, AccountType
    from app.models.core import Account

    other = Account(name="다른 계좌", type=AccountType.cash, side=AccountSide.asset)
    session.add(other)
    session.commit()
    session.refresh(other)

    client.post("/transactions", json=_payload(account.id))
    client.post("/transactions", json=_payload(other.id))

    rows = client.get("/transactions", params={"account_id": account.id}).json()

    assert len(rows) == 1
    assert rows[0]["account_id"] == account.id
