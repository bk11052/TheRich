"""규칙엔진(app/services/classify.py) 단위 테스트.

이 프로젝트에서 가장 고유한 로직이라 경계 조건까지 본다.
"""

from sqlmodel import Session

from app.models.base import MatchType
from app.services.classify import classify


def test_returns_none_when_merchant_is_empty(session: Session):
    assert classify(session, None) is None
    assert classify(session, "") is None


def test_contains_rule_matches_substring(session: Session, make_category, make_rule):
    cafe = make_category("카페/간식")
    make_rule("스타벅스", cafe.id, MatchType.contains)

    assert classify(session, "스타벅스 강남R점") == cafe.id


def test_exact_rule_requires_full_equality(session: Session, make_category, make_rule):
    cafe = make_category("카페/간식")
    make_rule("스타벅스", cafe.id, MatchType.exact)

    assert classify(session, "스타벅스") == cafe.id
    assert classify(session, "스타벅스 강남R점") is None  # 부분일치는 안 됨


def test_regex_rule_matches_pattern(session: Session, make_category, make_rule):
    conv = make_category("편의점")
    make_rule(r"^(GS25|CU|세븐일레븐)", conv.id, MatchType.regex)

    assert classify(session, "GS25 역삼점") == conv.id
    assert classify(session, "이마트24 강남") is None


def test_higher_priority_rule_wins(session: Session, make_category, make_rule):
    """같은 가맹점에 두 규칙이 걸리면 priority 가 높은 쪽이 이긴다."""
    general = make_category("식비")
    specific = make_category("배달")
    make_rule("배달", general.id, MatchType.contains, priority=1)
    make_rule("배달의민족", specific.id, MatchType.contains, priority=10)

    assert classify(session, "배달의민족") == specific.id


def test_disabled_rule_is_ignored(session: Session, make_category, make_rule):
    cafe = make_category("카페/간식")
    make_rule("스타벅스", cafe.id, MatchType.contains, enabled=False)

    assert classify(session, "스타벅스 강남R점") is None


def test_invalid_regex_does_not_crash_and_falls_through(
    session: Session, make_category, make_rule
):
    """깨진 정규식 규칙이 하나 있어도 전체가 죽지 않고 다음 규칙으로 넘어가야 한다."""
    broken = make_category("깨진규칙")
    cafe = make_category("카페/간식")
    make_rule("[", broken.id, MatchType.regex, priority=99)  # 컴파일 불가
    make_rule("스타벅스", cafe.id, MatchType.contains, priority=1)

    assert classify(session, "스타벅스 강남R점") == cafe.id


def test_returns_none_when_no_rule_matches(session: Session, make_category, make_rule):
    cafe = make_category("카페/간식")
    make_rule("스타벅스", cafe.id, MatchType.contains)

    assert classify(session, "이름없는가게") is None
