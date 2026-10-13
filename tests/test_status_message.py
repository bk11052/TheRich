"""봇이 보낼 텍스트 포맷. 사람이 읽는 출력이라 내용이 맞는지만 본다."""

from app.services.shared_budget import compute_status, format_status_message


def _spend(client, account_id, category_id, amount, payer_id=None):
    return client.post("/transactions", json={
        "account_id": account_id, "type": "expense", "amount": amount,
        "occurred_at": "2026-10-05T19:00:00",
        "category_id": category_id, "payer_id": payer_id,
    })


def test_message_without_config_explains_setup():
    msg = format_status_message(None)

    assert "설정" in msg


def test_message_shows_spent_limit_and_remaining(session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 200_000)

    msg = format_status_message(compute_status(session, "2026-10"))

    assert "200,000원" in msg
    assert "500,000원" in msg
    assert "300,000원 남음" in msg
    assert "40.0%" in msg


def test_message_reports_overspend_as_excess_not_negative(
    session, client, account, date_budget
):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 620_000)

    msg = format_status_message(compute_status(session, "2026-10"))

    assert "넘었" in msg
    assert "120,000원 초과" in msg
    assert "-120,000" not in msg  # 음수를 그대로 보여주지 않는다


def test_message_warns_near_limit(session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 420_000)  # 84%

    assert "얼마 안 남았" in format_status_message(compute_status(session, "2026-10"))


def test_message_omits_per_person_totals(session, client, account, date_budget, make_member):
    """결제자는 기록하지만 '누가 얼마 썼는지' 누적은 메시지에 넣지 않는다."""
    cat, _ = date_budget
    me = make_member("나", chat_id=111)
    her = make_member("여자친구", chat_id=222)
    _spend(client, account.id, cat.id, 50_000, payer_id=me.id)
    _spend(client, account.id, cat.id, 90_000, payer_id=her.id)

    msg = format_status_message(compute_status(session, "2026-10"))

    assert "여자친구" not in msg
    assert "90,000원" not in msg
    assert "140,000원" in msg  # 공동 합계만 보인다


def test_saved_line_is_prepended(session, client, account, date_budget):
    cat, _ = date_budget
    _spend(client, account.id, cat.id, 12_000)

    msg = format_status_message(
        compute_status(session, "2026-10"), saved="스타벅스 12,000원"
    )

    assert msg.splitlines()[0] == "기록했어요 — 스타벅스 12,000원"
