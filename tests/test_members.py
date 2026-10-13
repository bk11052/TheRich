"""멤버 CRUD. chat_id 는 봇 인증에 쓰이므로 중복 등록을 막는 게 핵심."""

from fastapi.testclient import TestClient


def test_create_member(client: TestClient):
    res = client.post("/members", json={"name": "여자친구", "telegram_chat_id": 222})

    assert res.status_code == 201
    assert res.json()["name"] == "여자친구"
    assert res.json()["active"] is True


def test_duplicate_chat_id_is_rejected(client: TestClient):
    client.post("/members", json={"name": "나", "telegram_chat_id": 111})

    res = client.post("/members", json={"name": "사칭", "telegram_chat_id": 111})

    assert res.status_code == 409


def test_members_without_chat_id_can_coexist(client: TestClient):
    """chat_id 가 없는(텔레그램 미사용) 멤버는 여럿이어도 된다."""
    assert client.post("/members", json={"name": "A"}).status_code == 201
    assert client.post("/members", json={"name": "B"}).status_code == 201


def test_list_excludes_inactive_by_default(client: TestClient):
    created = client.post("/members", json={"name": "탈퇴자"}).json()
    client.patch(f"/members/{created['id']}", json={"active": False})

    def names(active_only: bool) -> set[str]:
        rows = client.get("/members", params={"active_only": active_only}).json()
        return {m["name"] for m in rows}

    assert "탈퇴자" not in names(True)
    assert "탈퇴자" in names(False)


def test_get_missing_member_returns_404(client: TestClient):
    assert client.get("/members/9999").status_code == 404
