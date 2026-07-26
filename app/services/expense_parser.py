"""텔레그램 텍스트 지출 입력 파서.

"스타벅스 5500", "5,500원 스타벅스", "점심 김밥천국 8000" 같은 자유 텍스트에서
금액과 가맹점을 뽑아낸다. 규칙 기반(순수 함수) — 테스트 쉬움.
"""

import re
from dataclasses import dataclass

# "만원" 단위 지원: "3만" → 30000, "3만5천" 은 미지원(단순화)
_MAN = re.compile(r"(\d+(?:[.,]\d+)?)\s*만원?")
_NUM = re.compile(r"\d[\d,]*")


@dataclass
class ParsedExpense:
    amount: int  # 원 (정수)
    merchant: str | None


def parse_expense(text: str) -> ParsedExpense | None:
    """텍스트 → ParsedExpense. 금액을 못 찾으면 None.

    금액 규칙: '3만'류가 있으면 그걸 우선, 아니면 숫자 중 최댓값을 금액으로.
    가맹점: 금액/단위/조사 토큰을 제거한 나머지.
    """
    if not text:
        return None
    text = text.strip()

    amount: int | None = None
    working = text

    # 1) "N만(원)" 우선 처리
    man = _MAN.search(working)
    if man:
        amount = int(round(float(man.group(1).replace(",", "")) * 10_000))
        working = working[: man.start()] + " " + working[man.end() :]

    # 2) 일반 숫자들
    nums = [int(n.replace(",", "")) for n in _NUM.findall(working)]
    if amount is None:
        if not nums:
            return None
        amount = max(nums)

    if amount <= 0:
        return None

    # 가맹점: 숫자·만원·원·흔한 조사/필러 제거
    merchant = _MAN.sub(" ", text)
    merchant = _NUM.sub(" ", merchant)
    merchant = re.sub(r"원|씀|썼|결제|지출", " ", merchant)
    merchant = re.sub(r"\s+", " ", merchant).strip()

    return ParsedExpense(amount=amount, merchant=merchant or None)


_AMOUNT_WON = re.compile(r"([\d,]{2,})\s*원")
_WON_SIGN = re.compile(r"[₩\\]\s*([\d,]{2,})")
_HANGUL = re.compile(r"[가-힣]")
# 영수증/결제화면 라벨 — 가맹점명으로 오인 방지
_LABELS = (
    "승인", "취소", "합계", "금액", "결제", "카드", "일시", "가맹", "할부",
    "포인트", "잔액", "주소", "전화", "사업자", "매출", "부가세", "공급가",
    "TEL", "tel", "No", "님",
)


def parse_receipt(text: str) -> ParsedExpense | None:
    """결제 스크린샷 OCR 텍스트(멀티라인) → 금액·가맹점 추정.

    금액: 'N원'/'₩N' 패턴 중 최댓값(=총액) 우선, 없으면 3자리+ 숫자 최댓값.
    가맹점: 한글이 있고 숫자 비중이 낮으며 라벨이 아닌 첫 줄.
    """
    if not text:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    amounts: list[int] = []
    for m in _AMOUNT_WON.finditer(text):
        amounts.append(int(m.group(1).replace(",", "")))
    for m in _WON_SIGN.finditer(text):
        amounts.append(int(m.group(1).replace(",", "")))
    if not amounts:
        for n in re.findall(r"[\d,]{3,}", text):
            v = int(n.replace(",", ""))
            if v >= 100:
                amounts.append(v)
    if not amounts:
        return None
    amount = max(amounts)

    merchant: str | None = None
    for ln in lines:
        if not _HANGUL.search(ln):
            continue
        if any(lb in ln for lb in _LABELS):
            continue
        digits = sum(c.isdigit() for c in ln)
        if digits > len(ln) // 2:
            continue
        if len(ln) < 2:
            continue
        merchant = ln
        break

    return ParsedExpense(amount=amount, merchant=merchant)


# --- 셀프테스트: python -m app.services.expense_parser ---
if __name__ == "__main__":
    cases = [
        ("스타벅스 5500", 5500, "스타벅스"),
        ("5,500원 스타벅스", 5500, "스타벅스"),
        ("점심 김밥천국 8000", 8000, "점심 김밥천국"),
        ("택시 19000", 19000, "택시"),
        ("올리브영 3만2천원", 30000, "올리브영 2천"),  # 만원 우선(간이)
        ("배민 3만", 30000, "배민"),
        ("그냥 메모", None, None),
    ]
    ok = 0
    for text, exp_amt, exp_merch in cases:
        r = parse_expense(text)
        got_amt = r.amount if r else None
        got_merch = r.merchant if r else None
        status = "OK" if got_amt == exp_amt else "FAIL"
        if got_amt == exp_amt:
            ok += 1
        print(f"[{status}] {text!r:30} → amount={got_amt} merchant={got_merch!r}")
    print(f"\n{ok}/{len(cases)} amount matched")
