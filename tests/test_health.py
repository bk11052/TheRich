"""가장 단순한 경로. 앱이 조립되고 라우팅이 동작하는지 확인하는 연기 테스트."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    res = client.get("/health")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"
