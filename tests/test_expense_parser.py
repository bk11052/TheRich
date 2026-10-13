"""텔레그램 입력 파서(app/services/expense_parser.py) 테스트.

DB 를 안 타는 순수 함수라 입출력만 본다.
"""

import pytest

from app.services.expense_parser import parse_expense, parse_receipt


@pytest.mark.parametrize(
    "text, amount, merchant",
    [
        ("스타벅스 4500", 4500, "스타벅스"),
        ("스타벅스 4,500원", 4500, "스타벅스"),
        ("점심 12000", 12000, "점심"),
    ],
)
def test_parse_expense_reads_plain_number(text, amount, merchant):
    got = parse_expense(text)

    assert got is not None
    assert got.amount == amount
    assert got.merchant == merchant


def test_man_notation_wins_over_bare_number():
    """'3만'이 있으면 다른 숫자가 더 커도 '3만'을 금액으로 본다."""
    got = parse_expense("이마트 3만")

    assert got.amount == 30_000


def test_decimal_man_notation():
    assert parse_expense("회식 1.5만").amount == 15_000


def test_largest_number_is_taken_when_no_man_notation():
    got = parse_expense("GS25 역삼 2호점 8000")

    assert got.amount == 8000


@pytest.mark.parametrize("text", ["", "   ", "메모만 있고 숫자 없음"])
def test_returns_none_without_amount(text):
    assert parse_expense(text) is None


def test_zero_or_negative_amount_is_rejected():
    assert parse_expense("이상한거 0") is None


def test_parse_receipt_picks_amount_with_won_marker():
    ocr_text = "\n".join([
        "카카오페이",
        "스타벅스 강남R점",
        "2026-07-26",
        "결제금액",
        "12,500원",
    ])

    got = parse_receipt(ocr_text)

    assert got is not None
    assert got.amount == 12_500
    assert got.merchant == "스타벅스 강남R점"


def test_parse_receipt_returns_none_on_garbage():
    assert parse_receipt("아무 의미 없는 줄\n또 다른 줄") is None


def test_parse_receipt_skips_payment_app_name_at_top():
    """결제앱 스크린샷 최상단의 앱 이름을 가맹점으로 잡으면 안 된다."""
    got = parse_receipt("토스\n메가커피 역삼점\n결제금액\n2,500원")

    assert got.merchant == "메가커피 역삼점"


def test_parse_receipt_keeps_real_merchant_containing_app_brand():
    """반대로 '토스뱅크 창동점'처럼 상호 자체가 브랜드명을 포함하면 살아야 한다."""
    got = parse_receipt("카카오페이\n토스뱅크 창동점\n결제금액\n3,000원")

    assert got.merchant == "토스뱅크 창동점"
