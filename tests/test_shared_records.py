"""partner 의 기록(사진·장소·태그) 접근. 데이트비용 거래만 보고 만질 수 있어야 한다."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.core import Transaction
from app.models.lifelog import Photo, Place

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32  # 내용 검증은 안 하므로 헤더만 흉내


@pytest.fixture(autouse=True)
def _uploads_in_tmp(tmp_path, monkeypatch):
    """업로드가 실제 uploads/ 폴더에 쌓이지 않게."""
    from app.services import lifelog

    monkeypatch.setattr(lifelog, "UPLOAD_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def txns(session: Session, account, date_budget, make_category):
    """공유(데이트) 거래 하나와 owner 개인 거래 하나."""
    cat, _ = date_budget
    personal_cat = make_category("내 혼밥")
    shared = Transaction(account_id=account.id, type="expense", amount=30_000,
                         occurred_at=datetime(2026, 10, 5, 19), merchant="놀이공원",
                         category_id=cat.id)
    personal = Transaction(account_id=account.id, type="expense", amount=9_000,
                           occurred_at=datetime(2026, 10, 6, 12), merchant="혼자간식당",
                           category_id=personal_cat.id)
    session.add_all([shared, personal])
    session.commit()
    session.refresh(shared)
    session.refresh(personal)
    return shared, personal


def _photo(session: Session, txn_id: int):
    session.add(Photo(transaction_id=txn_id, file_path=f"/uploads/{txn_id}.png"))
    session.commit()


# ---------- 조회 ----------

def test_partner_records_show_only_shared_transactions(
    partner_client: TestClient, session, txns
):
    shared, personal = txns
    _photo(session, shared.id)
    _photo(session, personal.id)

    merchants = [r["merchant"] for r in partner_client.get("/shared/records").json()]

    assert merchants == ["놀이공원"]


def test_owner_records_still_show_everything(client: TestClient, session, txns):
    shared, personal = txns
    _photo(session, shared.id)
    _photo(session, personal.id)

    merchants = {r["merchant"] for r in client.get("/records").json()}

    assert merchants == {"놀이공원", "혼자간식당"}


@pytest.mark.parametrize("path", ["/records", "/photos", "/places", "/tags"])
def test_partner_still_cannot_use_owner_lifelog_routes(partner_client: TestClient, path):
    assert partner_client.get(path).status_code == 403


# ---------- 사진 ----------

def test_partner_can_upload_photo_to_shared_transaction(
    partner_client: TestClient, txns, _uploads_in_tmp
):
    shared, _ = txns
    res = partner_client.post(
        "/shared/photos",
        data={"transaction_id": str(shared.id)},
        files={"file": ("ride.png", PNG, "image/png")},
    )

    assert res.status_code == 201
    saved = res.json()["file_path"].rsplit("/", 1)[-1]
    assert (_uploads_in_tmp / saved).exists()


def test_partner_cannot_upload_photo_to_personal_transaction(partner_client: TestClient, txns):
    _, personal = txns
    res = partner_client.post(
        "/shared/photos",
        data={"transaction_id": str(personal.id)},
        files={"file": ("x.png", PNG, "image/png")},
    )

    # 403 이 아니라 404 — 그런 거래가 있다는 것도 알려주지 않는다.
    assert res.status_code == 404


def test_partner_svg_upload_is_rejected(partner_client: TestClient, txns):
    """SVG 는 스크립트를 품을 수 있고 API 와 같은 출처에서 서빙된다."""
    shared, _ = txns
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    res = partner_client.post(
        "/shared/photos",
        data={"transaction_id": str(shared.id)},
        files={"file": ("x.svg", svg, "image/svg+xml")},
    )

    assert res.status_code == 400


def test_owner_photo_upload_behaviour_unchanged(client: TestClient, txns):
    """리팩터 후에도 owner 업로드는 그대로 동작해야 한다(SVG 포함)."""
    shared, _ = txns
    for name, body, mime in (("a.png", PNG, "image/png"), ("b.svg", b"<svg/>", "image/svg+xml")):
        res = client.post("/photos", data={"transaction_id": str(shared.id)},
                          files={"file": (name, body, mime)})
        assert res.status_code == 201, name


def test_oversized_photo_is_rejected(partner_client: TestClient, txns, monkeypatch):
    from app.services import lifelog

    monkeypatch.setattr(lifelog, "MAX_PHOTO_BYTES", 10)
    shared, _ = txns
    res = partner_client.post("/shared/photos", data={"transaction_id": str(shared.id)},
                              files={"file": ("big.png", PNG, "image/png")})

    assert res.status_code == 413


# ---------- 태그 ----------

def test_partner_can_tag_shared_transaction(partner_client: TestClient, txns):
    shared, _ = txns
    tag = partner_client.post("/shared/tags", json={"name": "놀이공원"}).json()

    res = partner_client.put(f"/shared/transactions/{shared.id}/tags", json={"tag_ids": [tag["id"]]})

    assert res.status_code == 200
    assert [t["name"] for t in res.json()] == ["놀이공원"]


def test_partner_cannot_tag_personal_transaction(partner_client: TestClient, txns):
    _, personal = txns
    tag = partner_client.post("/shared/tags", json={"name": "몰래"}).json()

    res = partner_client.put(f"/shared/transactions/{personal.id}/tags", json={"tag_ids": [tag["id"]]})

    assert res.status_code == 404


# ---------- 메모 ----------

def test_partner_can_edit_memo_but_not_amount(partner_client: TestClient, session, txns):
    shared, _ = txns
    res = partner_client.patch(
        f"/shared/transactions/{shared.id}", json={"memo": "회전목마 탐", "amount": 1}
    )

    assert res.status_code == 200
    session.refresh(shared)
    assert shared.memo == "회전목마 탐"
    assert shared.amount == 30_000  # amount 는 무시돼야 한다


def test_partner_cannot_edit_personal_transaction(partner_client: TestClient, txns):
    _, personal = txns

    assert partner_client.patch(f"/shared/transactions/{personal.id}", json={"memo": "x"}).status_code == 404


# ---------- 장소 ----------

def test_partner_attach_place_creates_a_new_place(partner_client: TestClient, session, txns):
    shared, _ = txns
    res = partner_client.post(f"/shared/transactions/{shared.id}/place", json={"name": "롯데월드"})

    assert res.status_code == 201
    session.refresh(shared)
    assert session.get(Place, shared.place_id).name == "롯데월드"


def test_partner_cannot_pull_in_an_existing_private_place(
    partner_client: TestClient, session, txns
):
    """기존 place_id 를 넣어도 무시되고 새 장소가 만들어져야 한다.
    아니면 번호만 바꿔가며 owner 의 개인 장소(주소·좌표)를 공유 기록으로 끌어올 수 있다."""
    shared, personal = txns
    secret = Place(name="집 근처 단골집", address="비밀 주소", lat=37.1, lng=127.1)
    session.add(secret)
    session.commit()
    session.refresh(secret)
    personal.place_id = secret.id
    session.add(personal)
    session.commit()

    partner_client.post(
        f"/shared/transactions/{shared.id}/place",
        json={"name": "어딘가", "id": secret.id, "place_id": secret.id},
    )

    rec = partner_client.get("/shared/records").json()[0]
    assert rec["place"]["id"] != secret.id
    assert "비밀 주소" not in str(partner_client.get("/shared/records").json())


def test_partner_cannot_attach_place_to_personal_transaction(partner_client: TestClient, txns):
    _, personal = txns

    assert partner_client.post(
        f"/shared/transactions/{personal.id}/place", json={"name": "x"}
    ).status_code == 404


# ---------- 내 정보 ----------

def test_partner_can_change_own_color(partner_client: TestClient, session, partner):
    res = partner_client.patch("/shared/me", json={"color": "보라"})

    assert res.status_code == 200
    session.refresh(partner)
    assert partner.color == "#b05cd6"


def test_partner_color_must_be_valid(partner_client: TestClient):
    assert partner_client.patch("/shared/me", json={"color": "무지개"}).status_code == 422


def test_partner_cannot_rename_or_promote_self(partner_client: TestClient, session, partner):
    """이름(로그인 아이디)·역할은 /shared/me 로 바꿀 수 없다."""
    original = partner.name
    partner_client.patch("/shared/me", json={"color": "#123456", "name": "해커", "role": "owner"})

    session.refresh(partner)
    assert partner.name == original
    assert partner.role.value == "partner"
