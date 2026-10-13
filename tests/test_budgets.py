"""예산 소진율 계산(GET /budgets/status) 테스트."""

from fastapi.testclient import TestClient


def _expense(client: TestClient, account_id: int, category_id: int, amount: int,
             when: str = "2026-07-10T12:00:00"):
    return client.post("/transactions", json={
        "account_id": account_id, "type": "expense", "amount": amount,
        "occurred_at": when, "category_id": category_id,
    })


def test_status_computes_spent_and_remaining(client: TestClient, account, make_category):
    cafe = make_category("카페/간식")
    client.post("/budgets", json={"category_id": cafe.id, "period_month": "2026-07", "amount": 100_000})
    _expense(client, account.id, cafe.id, 30_000)
    _expense(client, account.id, cafe.id, 20_000)

    row = client.get("/budgets/status", params={"month": "2026-07"}).json()[0]

    assert row["spent"] == 50_000
    assert row["remaining"] == 50_000
    assert row["usage"] == 0.5


def test_status_ignores_transactions_from_other_months(
    client: TestClient, account, make_category
):
    cafe = make_category("카페/간식")
    client.post("/budgets", json={"category_id": cafe.id, "period_month": "2026-07", "amount": 100_000})
    _expense(client, account.id, cafe.id, 30_000, when="2026-07-10T12:00:00")
    _expense(client, account.id, cafe.id, 90_000, when="2026-08-01T12:00:00")  # 다음 달

    row = client.get("/budgets/status", params={"month": "2026-07"}).json()[0]

    assert row["spent"] == 30_000


def test_status_ignores_other_categories(client: TestClient, account, make_category):
    cafe = make_category("카페/간식")
    food = make_category("식비")
    client.post("/budgets", json={"category_id": cafe.id, "period_month": "2026-07", "amount": 100_000})
    _expense(client, account.id, cafe.id, 10_000)
    _expense(client, account.id, food.id, 70_000)

    row = client.get("/budgets/status", params={"month": "2026-07"}).json()[0]

    assert row["spent"] == 10_000


def test_status_with_no_spending_is_zero_not_error(client: TestClient, make_category):
    cafe = make_category("카페/간식")
    client.post("/budgets", json={"category_id": cafe.id, "period_month": "2026-07", "amount": 100_000})

    row = client.get("/budgets/status", params={"month": "2026-07"}).json()[0]

    assert row["spent"] == 0
    assert row["usage"] == 0.0


def test_status_can_exceed_100_percent(client: TestClient, account, make_category):
    """초과 지출을 음수 remaining 으로 그대로 드러내야 한다(clamp 하지 않음)."""
    cafe = make_category("카페/간식")
    client.post("/budgets", json={"category_id": cafe.id, "period_month": "2026-07", "amount": 50_000})
    _expense(client, account.id, cafe.id, 80_000)

    row = client.get("/budgets/status", params={"month": "2026-07"}).json()[0]

    assert row["remaining"] == -30_000
    assert row["usage"] == 1.6
