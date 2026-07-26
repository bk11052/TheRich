"""기본 카테고리 + 가맹점 자동분류 규칙 시드.

실행: python -m app.seed
재실행 안전(idempotent) — 이름/패턴 중복은 건너뜀. 규칙은 언제든 API로 수정 가능.
"""

from sqlmodel import Session, select

from app.db import engine
from app.models.base import CategoryKind, MatchType
from app.models.core import Category, CategoryRule

# (name, kind, icon, is_fixed)
CATEGORIES: list[tuple[str, CategoryKind, str, bool]] = [
    ("식비", CategoryKind.expense, "🍚", False),
    ("배달", CategoryKind.expense, "🛵", False),
    ("카페/간식", CategoryKind.expense, "☕", False),
    ("편의점", CategoryKind.expense, "🏪", False),
    ("마트/장보기", CategoryKind.expense, "🛒", False),
    ("교통", CategoryKind.expense, "🚌", False),
    ("통신", CategoryKind.expense, "📱", True),
    ("주거/월세", CategoryKind.expense, "🏠", True),
    ("관리비/공과금", CategoryKind.expense, "🧾", True),
    ("구독", CategoryKind.expense, "🔁", True),
    ("보험", CategoryKind.expense, "🛡️", True),
    ("쇼핑", CategoryKind.expense, "🛍️", False),
    ("의류/미용", CategoryKind.expense, "💇", False),
    ("의료/건강", CategoryKind.expense, "💊", False),
    ("문화/여가", CategoryKind.expense, "🎬", False),
    ("여행", CategoryKind.expense, "✈️", False),
    ("교육", CategoryKind.expense, "📚", False),
    ("경조사", CategoryKind.expense, "🎁", False),
    ("세금/수수료", CategoryKind.expense, "🏛️", False),
    ("기타지출", CategoryKind.expense, "🔖", False),
    ("급여", CategoryKind.income, "💰", False),
    ("용돈", CategoryKind.income, "🪙", False),
    ("이자/배당", CategoryKind.income, "📈", False),
    ("환급/캐시백", CategoryKind.income, "💸", False),
    ("기타수입", CategoryKind.income, "➕", False),
]

# (pattern, category_name, priority) — 전부 contains 매칭.
# priority 높을수록 먼저 검사 → 구체 브랜드가 일반 키워드를 이김
# (예: "쿠팡이츠"(배달, 10)가 "쿠팡"(쇼핑, 1)보다 우선).
RULES: list[tuple[str, str, int]] = [
    # 식비 (일반 음식점 — 낮은 우선순위, 배달/카페 브랜드가 우선)
    ("식당", "식비", 1), ("국밥", "식비", 1), ("김밥", "식비", 1), ("백반", "식비", 1),
    ("분식", "식비", 1), ("치킨", "식비", 1), ("피자", "식비", 1), ("고깃집", "식비", 1),
    ("삼겹", "식비", 1), ("냉면", "식비", 1), ("칼국수", "식비", 1), ("떡볶이", "식비", 1),
    ("곱창", "식비", 1), ("횟집", "식비", 1), ("맛집", "식비", 1),
    # 배달
    ("배달의민족", "배달", 10), ("배민", "배달", 10), ("쿠팡이츠", "배달", 10), ("요기요", "배달", 10),
    # 카페/간식
    ("스타벅스", "카페/간식", 10), ("투썸", "카페/간식", 10), ("이디야", "카페/간식", 10),
    ("메가커피", "카페/간식", 10), ("컴포즈", "카페/간식", 10), ("폴바셋", "카페/간식", 10),
    ("빽다방", "카페/간식", 10), ("커피", "카페/간식", 1), ("카페", "카페/간식", 1),
    # 편의점
    ("GS25", "편의점", 10), ("세븐일레븐", "편의점", 10), ("이마트24", "편의점", 10),
    ("미니스톱", "편의점", 10), ("씨유", "편의점", 10),
    # 마트/장보기
    ("홈플러스", "마트/장보기", 10), ("롯데마트", "마트/장보기", 10), ("코스트코", "마트/장보기", 10),
    ("이마트", "마트/장보기", 5), ("마트", "마트/장보기", 1),
    # 교통
    ("카카오 T", "교통", 10), ("카카오모빌리티", "교통", 10), ("티머니", "교통", 10),
    ("지하철", "교통", 10), ("코레일", "교통", 10), ("SRT", "교통", 10),
    ("GS칼텍스", "교통", 10), ("SK에너지", "교통", 10), ("현대오일뱅크", "교통", 10),
    ("주유", "교통", 5), ("택시", "교통", 5), ("버스", "교통", 5),
    # 통신
    ("SK텔레콤", "통신", 10), ("LG U+", "통신", 10), ("유플러스", "통신", 10), ("헬로모바일", "통신", 10),
    # 구독
    ("넷플릭스", "구독", 10), ("NETFLIX", "구독", 10), ("유튜브", "구독", 10), ("YouTube", "구독", 10),
    ("디즈니", "구독", 10), ("티빙", "구독", 10), ("웨이브", "구독", 10), ("왓챠", "구독", 10),
    ("스포티파이", "구독", 10), ("Spotify", "구독", 10), ("멜론", "구독", 10),
    ("OpenAI", "구독", 10), ("ChatGPT", "구독", 10), ("Claude", "구독", 10),
    # 쇼핑 / 의류·미용
    ("올리브영", "의류/미용", 10), ("무신사", "의류/미용", 10),
    ("29CM", "쇼핑", 10), ("지마켓", "쇼핑", 10), ("11번가", "쇼핑", 10), ("옥션", "쇼핑", 10),
    ("다이소", "쇼핑", 10), ("쿠팡", "쇼핑", 1), ("네이버페이", "쇼핑", 1),
    # 의료/건강
    ("병원", "의료/건강", 10), ("약국", "의료/건강", 10), ("치과", "의료/건강", 10),
    ("한의원", "의료/건강", 10), ("의원", "의료/건강", 5),
    # 문화/여가
    ("CGV", "문화/여가", 10), ("롯데시네마", "문화/여가", 10), ("메가박스", "문화/여가", 10),
    ("PC방", "문화/여가", 10), ("노래방", "문화/여가", 10), ("필라테스", "문화/여가", 10),
    ("헬스", "문화/여가", 5),
    # 교육
    ("교보문고", "교육", 10), ("알라딘", "교육", 10), ("YES24", "교육", 10),
    ("인프런", "교육", 10), ("학원", "교육", 5),
]


def seed() -> None:
    with Session(engine) as session:
        # --- 카테고리 (이름 기준 idempotent) ---
        existing = {c.name for c in session.exec(select(Category)).all()}
        added_cat = 0
        for name, kind, icon, is_fixed in CATEGORIES:
            if name in existing:
                continue
            session.add(Category(name=name, kind=kind, icon=icon, is_fixed=is_fixed))
            added_cat += 1
        session.commit()

        cat_by_name = {c.name: c for c in session.exec(select(Category)).all()}

        # --- 규칙 (패턴 기준 idempotent) ---
        existing_patterns = {r.pattern for r in session.exec(select(CategoryRule)).all()}
        added_rule = 0
        for pattern, cat_name, priority in RULES:
            if pattern in existing_patterns:
                continue
            cat = cat_by_name.get(cat_name)
            if cat is None:
                continue
            session.add(
                CategoryRule(
                    pattern=pattern,
                    category_id=cat.id,
                    match_type=MatchType.contains,
                    priority=priority,
                )
            )
            existing_patterns.add(pattern)
            added_rule += 1
        session.commit()

        total_rules = len(session.exec(select(CategoryRule)).all())
        print(f"categories: +{added_cat} (total {len(cat_by_name)})")
        print(f"rules:      +{added_rule} (total {total_rules})")


if __name__ == "__main__":
    seed()
